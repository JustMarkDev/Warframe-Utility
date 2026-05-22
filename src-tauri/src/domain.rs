use serde::{Serialize, Deserialize};
use std::fmt;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct SyndicateState {
    pub faction_key: String,
    pub standing: i32,
    pub rank: i32,
}

impl SyndicateState {
    pub fn new(faction_key: &str, standing: i32, rank: i32) -> Self {
        Self {
            faction_key: faction_key.to_string(),
            standing,
            rank,
        }
    }

    pub fn max_standing(&self) -> i32 {
        match self.rank {
            5 => 132000,
            4 => 99000,
            3 => 70000,
            2 => 44000,
            1 => 22000,
            _ => 5000,
        }
    }

    pub fn listable_quantity(&self) -> i32 {
        let cost = get_syndicate_cost(&self.faction_key);
        self.standing / cost
    }
}

pub fn get_syndicate_cost(_faction_key: &str) -> i32 {
    25000
}

#[derive(Debug, Serialize, Clone)]
#[serde(tag = "type", content = "data")]
pub enum AppError {
    Overlap {
        item_slug: String,
        eligible_factions: Vec<String>,
    },
    InsufficientStanding {
        item_slug: String,
    },
    Io(String),
    Network(String),
    Other(String),
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            AppError::Overlap { item_slug, eligible_factions } => {
                write!(f, "Item '{}' belongs to multiple eligible factions: {:?}", item_slug, eligible_factions)
            }
            AppError::InsufficientStanding { item_slug } => {
                write!(f, "No represented faction has enough standing to sell '{}'", item_slug)
            }
            AppError::Io(err) => write!(f, "IO Error: {}", err),
            AppError::Network(err) => write!(f, "Network/API Error: {}", err),
            AppError::Other(err) => write!(f, "{}", err),
        }
    }
}

impl std::error::Error for AppError {}

impl From<std::io::Error> for AppError {
    fn from(err: std::io::Error) -> Self {
        AppError::Io(err.to_string())
    }
}

impl From<reqwest::Error> for AppError {
    fn from(err: reqwest::Error) -> Self {
        AppError::Network(err.to_string())
    }
}

pub fn get_syndicate_mods(faction_key: &str, current_rank: i32) -> Vec<&'static str> {
    let mut mods = Vec::new();
    for r in 0..=current_rank {
        mods.extend(get_syndicate_mods_at_rank(faction_key, r));
    }
    mods
}

pub fn get_syndicate_mods_at_rank(faction: &str, rank: i32) -> Vec<&'static str> {
    match (faction, rank) {
        ("steel_meridian", 4) => vec![
            "scattered_justice",
            "justice_blades",
            "neutralizing_justice",
            "shattering_justice",
        ],
        ("steel_meridian", 5) => vec![
            "path_of_statues", "tectonic_fracture", "ore_gaze", "titanic_rumbler", "rubble_heap",
            "recrystalize",
            "fireball_frenzy", "immolated_radiance", "healing_flame", "exothermic",
            "surging_dash", "radiant_finish", "furious_javelin", "chromatic_blade",
            "freeze_force", "ice_wave_impedance", "chilling_globe", "icy_avalanche", "biting_frost",
            "dread_ward", "blood_forge", "blending_talons",
            "gourmand", "hearty_nourishment", "catapult",
            "accumulating_whipclaw", "venari_bodyguard", "pilfering_strangledome",
            "wrath_of_ukko",
            "ballistic_bullseye", "staggering_shield", "muzzle_flash", "mesas_waltz",
            "pyroclastic_flow", "reaping_chakram", "safeguard", "divine_retribution", "controlled_slide",
            "teeming_virulence", "larva_burst", "parasitic_vitality", "insatiable", "abundant_mutation",
            "neutron_star", "antimatter_absorb", "escape_velocity", "molecular_fission",
            "smite_infusion", "hallowed_eruption", "phoenix_renewal", "hallowed_reckoning",
            "ironclad_charge", "iron_shrapnel", "piercing_roar", "reinforcing_stomp",
            "venom_dose", "revealing_spores", "regenerative_molt", "contagion_cloud",
            "ulfruns_endurance",
            "vampiric_grasp", "the_relentless_lost",
        ],
        ("arbiters_of_hexis", 4) => vec![
            "gilded_truth", "blade_of_truth", "stinging_truth", "avenging_truth",
        ],
        ("arbiters_of_hexis", 5) => vec![
            "seeking_shuriken", "smoke_shadow", "fatal_teleport", "rising_storm",
            "elusive_retribution", "endless_lullaby", "reactive_storm",
            "duality", "calm_and_frenzy", "peaceful_provocation", "energy_transfer",
            "surging_dash", "radiant_finish", "furious_javelin", "chromatic_blade",
            "shattered_storm", "mending_splinters", "spectrosiphon",
            "mach_crash", "thermal_transfer",
            "coil_recharge", "cathode_current",
            "tribunal", "warding_thurible", "lasting_covenant",
            "elemental_sandstorm", "negation_swarm", "desiccations_curse",
            "rift_haven", "rift_torrent", "cataclysmic_continuum",
            "savior_decoy", "hushed_invisibility", "safeguard_switch", "irradiating_disarm", "damage_decoy",
            "hall_of_malevolence", "explosive_legerdemain", "total_eclipse",
            "mind_freak", "pacifying_bolts", "chaos_sphere", "assimilate",
            "repair_dispensary", "temporal_erosion", "temporal_artillery",
            "axios_javelineers", "intrepid_stand",
            "shock_trooper", "shocking_speed", "transistor_shield", "capacitance",
            "celestial_stomp", "enveloping_cloud", "primal_rage",
            "merulina_guardian", "loyal_merulina", "surging_blades",
        ],
        ("cephalon_suda", 4) => vec![
            "entropy_spike", "entropy_flight", "entropy_detonation", "entropy_burst",
        ],
        ("cephalon_suda", 5) => vec![
            "sonic_fracture", "resonance", "savage_silence", "resonating_quake",
            "afterburn", "everlasting_ward", "guardian_armor", "vexing_retaliation", "guided_effigy",
            "freeze_force", "ice_wave_impedance", "chilling_globe", "icy_avalanche", "biting_frost",
            "balefire_surge", "blazing_pillage", "aegis_gale",
            "viral_tempest", "tidal_impunity", "rousing_plunder", "pilfering_swarm",
            "empowered_quiver", "piercing_navigator", "infiltrate", "concentrated_arrow",
            "rift_haven", "rift_torrent", "cataclysmic_continuum",
            "hall_of_malevolence", "explosive_legerdemain", "total_eclipse",
            "pyroclastic_flow", "reaping_chakram", "safeguard", "controlled_slide", "divine_retribution",
            "neutron_star", "antimatter_absorb", "escape_velocity", "molecular_fission",
            "partitioned_mallet", "conductor",
            "wrecking_wall",
            "thrall_pact", "mesmer_shield", "blinding_reave",
            "shadow_haze", "dark_propagation",
            "tesla_bank", "photon_repeater", "repelling_bastille",
        ],
        ("perrin_sequence", 4) => vec![
            "toxic_sequence", "deadly_sequence", "voltage_sequence", "sequence_burn",
        ],
        ("perrin_sequence", 5) => vec![
            "sonic_fracture", "resonance", "savage_silence", "resonating_quake",
            "afterburn", "everlasting_ward", "guardian_armor", "vexing_retaliation", "guided_effigy",
            "spectral_spirit",
            "mach_crash", "thermal_transfer",
            "coil_recharge", "cathode_current",
            "balefire_surge", "blazing_pillage", "aegis_gale",
            "elemental_sandstorm", "negation_swarm", "desiccations_curse",
            "empowered_quiver", "piercing_navigator", "infiltrate", "concentrated_arrow",
            "greedy_pull", "magnetized_discharge", "counter_pulse", "fracturing_crush",
            "soul_survivor", "creeping_terrify", "despoil", "shield_of_shadows",
            "teeming_virulence", "larva_burst", "parasitic_vitality", "insatiable", "abundant_mutation",
            "repair_dispensary", "temporal_erosion", "temporal_artillery",
            "thrall_pact", "mesmer_shield", "blinding_reave",
            "ironclad_charge", "iron_shrapnel", "piercing_roar", "reinforcing_stomp",
            "shadow_haze", "dark_propagation",
            "pool_of_life", "vampire_leech", "abating_link", "champions_blessing",
            "swing_line", "eternal_war", "prolonged_paralysis", "enraged", "hysterical_assault",
            "tesla_bank", "photon_repeater", "repelling_bastille",
        ],
        ("red_veil", 4) => vec![
            "gleaming_blight", "eroding_blight", "toxic_blight", "stockpiled_blight",
        ],
        ("red_veil", 5) => vec![
            "seeking_shuriken", "smoke_shadow", "fatal_teleport", "rising_storm",
            "path_of_statues", "tectonic_fracture", "ore_gaze", "titanic_rumbler", "rubble_heap",
            "recrystalize",
            "fireball_frenzy", "immolated_radiance", "healing_flame", "exothermic",
            "warriors_rest",
            "dread_ward", "blood_forge", "blending_talons",
            "gourmand", "hearty_nourishment", "catapult",
            "tribunal", "warding_thurible", "lasting_covenant",
            "accumulating_whipclaw", "venari_bodyguard", "pilfering_strangledome",
            "valence_formation", "swift_bite",
            "savior_decoy", "hushed_invisibility", "safeguard_switch", "irradiating_disarm", "damage_decoy",
            "ballistic_bullseye", "staggering_shield", "muzzle_flash", "mesas_waltz",
            "soul_survivor", "creeping_terrify", "despoil", "shield_of_shadows",
            "venom_dose", "revealing_spores", "regenerative_molt", "contagion_cloud",
            "spellbound_harvest", "beguiling_lantern", "razorwing_blitz", "ironclad_flight",
            "shock_trooper", "shocking_speed", "transistor_shield", "capacitance",
            "target_fixation", "airburst_rounds", "jet_stream", "funnel_clouds", "anchored_glide",
        ],
        ("new_loka", 4) => vec![
            "winds_of_purity", "bright_purity", "lasting_purity", "disarming_purity",
        ],
        ("new_loka", 5) => vec![
            "elusive_retribution", "endless_lullaby", "reactive_storm",
            "duality", "calm_and_frenzy", "peaceful_provocation", "energy_transfer",
            "shattered_storm", "mending_splinters", "spectrosiphon",
            "viral_tempest", "tidal_impunity", "rousing_plunder", "pilfering_swarm",
            "wrath_of_ukko",
            "valence_formation", "swift_bite",
            "greedy_pull", "magnetized_discharge", "counter_pulse", "fracturing_crush",
            "mind_freak", "pacifying_bolts", "chaos_sphere", "assimilate",
            "smite_infusion", "hallowed_eruption", "phoenix_renewal", "hallowed_reckoning",
            "partitioned_mallet", "conductor",
            "axios_javelineers", "intrepid_stand",
            "spellbound_harvest", "beguiling_lantern", "razorwing_blitz", "ironclad_flight",
            "pool_of_life", "vampire_leech", "abating_link", "champions_blessing",
            "swing_line", "eternal_war", "prolonged_paralysis", "enraged", "hysterical_assault",
            "fused_reservoir", "critical_surge",
            "celestial_stomp", "enveloping_cloud", "primal_rage",
            "merulina_guardian", "loyal_merulina", "surging_blades",
            "target_fixation", "airburst_rounds", "jet_stream", "funnel_clouds", "anchored_glide",
        ],
        _ => vec![],
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_syndicate_state_limits() {
        let state = SyndicateState::new("steel_meridian", 100000, 5);
        assert_eq!(state.standing, 100000);
        assert_eq!(state.rank, 5);
        assert_eq!(state.max_standing(), 132000);
        assert_eq!(state.listable_quantity(), 4);
    }

    #[test]
    fn test_standing_bounds_clamping_ranges() {
        let mut state = SyndicateState::new("steel_meridian", 150000, 5);
        let max_val = state.max_standing();
        state.standing = i32::min(150000, max_val);
        assert_eq!(state.standing, 132000);

        state.rank = 4;
        let max_val = state.max_standing();
        state.standing = i32::min(state.standing, max_val);
        assert_eq!(state.standing, 99000);
    }

    #[test]
    fn test_listable_quantity_calculations() {
        let mut state = SyndicateState::new("steel_meridian", 50000, 5);
        assert_eq!(state.listable_quantity(), 2);

        state.standing = 24999;
        assert_eq!(state.listable_quantity(), 0);

        state.standing = 0;
        assert_eq!(state.listable_quantity(), 0);
    }

    #[test]
    fn test_get_syndicate_mods() {
        let mods_rank5 = get_syndicate_mods("steel_meridian", 5);
        assert!(mods_rank5.contains(&"scattered_justice"));
        assert!(mods_rank5.contains(&"path_of_statues"));

        let mods_rank3 = get_syndicate_mods("steel_meridian", 3);
        assert_eq!(mods_rank3.len(), 0);
    }
}
