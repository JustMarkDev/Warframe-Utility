use serde::Serialize;
use crate::domain::{SyndicateState, AppError, get_syndicate_mods, get_syndicate_cost};
use crate::persistence::{load_all_standings, save_all_standings, load_jwt, save_jwt};
use crate::market::MarketClient;

const STATUS_PATH: &str = "syndicate_status.json";
const SETTINGS_PATH: &str = "settings.conf";

/// Syncs warframe.market sell listings for one faction to match the current
/// standing. If the faction has listable quantity > 0, every mod is posted or
/// undercut by 1 platinum. If standing has dropped to zero, every listing is
/// deleted. All market errors propagate — callers are responsible for deciding
/// whether to roll back any prior state changes.
async fn sync_listings(client: &MarketClient, state: &SyndicateState) -> Result<(), AppError> {
    let mods = get_syndicate_mods(&state.faction_key, state.rank);
    let qty = state.listable_quantity();

    if qty > 0 {
        for m in &mods {
            let lowest = client.get_lowest_price(m).await?;
            let price = match lowest {
                Some(p) => i32::max(1, p - 1),
                None => 10,
            };
            client.post_or_update_listing(m, qty, price).await?;
        }
    } else {
        for m in &mods {
            client.delete_listing(m).await?;
        }
    }

    Ok(())
}

#[derive(Serialize)]
pub struct InitData {
    pub standings: Vec<SyndicateState>,
    pub authenticated: bool,
    pub account_name: Option<String>,
}

#[tauri::command]
pub async fn load_syndicates() -> Result<InitData, AppError> {
    let standings_map = load_all_standings(STATUS_PATH).await?;
    let mut standings: Vec<SyndicateState> = standings_map.into_values().collect();
    // Sort for stable UI layout
    standings.sort_by(|a, b| a.faction_key.cmp(&b.faction_key));

    let token_opt = load_jwt(SETTINGS_PATH).await?;
    let mut authenticated = false;
    let mut account_name = None;

    if let Some(token) = token_opt {
        let client = MarketClient::new(&token);
        if let Ok(slug) = client.validate_token().await {
            authenticated = true;
            account_name = Some(slug);
        }
    }

    Ok(InitData {
        standings,
        authenticated,
        account_name,
    })
}

#[tauri::command]
pub async fn save_token(token: String) -> Result<String, AppError> {
    let client = MarketClient::new(&token);
    let slug = client.validate_token().await?;
    save_jwt(SETTINGS_PATH, &token).await?;
    Ok(slug)
}

#[tauri::command]
pub async fn update_standing(faction_key: String, standing: i32, rank: Option<i32>) -> Result<SyndicateState, AppError> {
    let mut standings = load_all_standings(STATUS_PATH).await?;
    
    let updated_state = if let Some(state) = standings.get_mut(&faction_key) {
        if let Some(r) = rank {
            state.rank = r;
        }
        let max_val = state.max_standing();
        state.standing = i32::min(i32::max(0, standing), max_val);
        state.clone()
    } else {
        return Err(AppError::Other(format!("Faction '{}' not found", faction_key)));
    };
    
    save_all_standings(STATUS_PATH, &standings).await?;
    Ok(updated_state)
}

#[tauri::command]
pub async fn publish_syndicate(faction_key: String) -> Result<Vec<String>, AppError> {
    let standings = load_all_standings(STATUS_PATH).await?;
    let state = standings.get(&faction_key)
        .ok_or_else(|| AppError::Other(format!("Faction '{}' not found", faction_key)))?;
    
    let token = load_jwt(SETTINGS_PATH).await?
        .ok_or_else(|| AppError::Other("Not authenticated with warframe.market. Please set token first.".to_string()))?;
    
    let client = MarketClient::new(&token);
    let available_mods = get_syndicate_mods(&faction_key, state.rank);

    sync_listings(&client, state).await?;

    Ok(available_mods.into_iter().map(|s| s.to_string()).collect())
}

#[tauri::command]
pub async fn record_sale(item_slug: String, quantity: i32, faction_choice: Option<String>) -> Result<String, AppError> {
    let mut standings = load_all_standings(STATUS_PATH).await?;
    let token = load_jwt(SETTINGS_PATH).await?
        .ok_or_else(|| AppError::Other("Not authenticated with warframe.market. Please set token first.".to_string()))?;
    
    let client = MarketClient::new(&token);
    let mut eligible_factions = Vec::new();

    for (key, state) in &standings {
        let available_mods = get_syndicate_mods(key, state.rank);
        let cost = get_syndicate_cost(key);
        
        if available_mods.contains(&item_slug.as_str()) && state.standing >= (cost * quantity) {
            eligible_factions.push(key.clone());
        }
    }

    if eligible_factions.is_empty() {
        return Err(AppError::InsufficientStanding { item_slug });
    }

    let chosen_faction = if eligible_factions.len() > 1 {
        match faction_choice {
            Some(ref choice) => {
                if eligible_factions.contains(choice) {
                    choice.clone()
                } else {
                    return Err(AppError::Other(format!("Chosen faction '{}' is not eligible to attribute this sale.", choice)));
                }
            }
            None => {
                return Err(AppError::Overlap {
                    item_slug,
                    eligible_factions,
                });
            }
        }
    } else {
        eligible_factions[0].clone()
    };

    // Process Deduction
    let cost = get_syndicate_cost(&chosen_faction);
    if let Some(state) = standings.get_mut(&chosen_faction) {
        state.standing -= cost * quantity;
    }
    
    save_all_standings(STATUS_PATH, &standings).await?;

    // Cascade Updates — sync listings atomically; if this fails the sale is
    // still committed to disk but the caller receives the error.
    let updated_state = standings.get(&chosen_faction).unwrap();
    sync_listings(&client, updated_state).await?;

    Ok(chosen_faction)
}

#[tauri::command]
pub fn get_faction_mods(faction_key: String, rank: i32) -> Result<Vec<String>, AppError> {
    let mods = get_syndicate_mods(&faction_key, rank);
    Ok(mods.into_iter().map(|s| s.to_string()).collect())
}

