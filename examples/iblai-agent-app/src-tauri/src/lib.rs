
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let mut builder = tauri::Builder::default()
        .plugin(tauri_plugin_opener::init());

    // On Android the webview blocks navigation to external URLs by default,
    // which prevents the SSO redirect to login.iblai.app from working.
    // We suppress the default window via tauri.android.conf.json ("windows": [])
    // and create it here with on_navigation to allow auth-domain navigation.
    #[cfg(target_os = "android")]
    {
        builder = builder.setup(|app| {
            use tauri::{WebviewUrl, WebviewWindowBuilder};
            WebviewWindowBuilder::new(app, "main", WebviewUrl::default())
                .title(app.config().product_name.clone().unwrap_or_default())
                .on_navigation(|url| {
                    let host = url.host_str().unwrap_or_default();
                    url.scheme() == "tauri"
                        || url.scheme() == "http"
                        || host == "localhost"
                        || host.starts_with("127.")
                        || host.starts_with("10.")
                        || host.starts_with("192.168.")
                        || host.ends_with(".iblai.app")
                        || host.ends_with(".iblai.org")
                })
                .build()?;
            Ok(())
        });
    }

    builder
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
