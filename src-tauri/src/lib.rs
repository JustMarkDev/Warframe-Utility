pub mod domain;
pub mod persistence;
pub mod market;
pub mod commands;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            commands::load_syndicates,
            commands::save_token,
            commands::update_standing,
            commands::publish_syndicate,
            commands::record_sale,
            commands::get_faction_mods
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
