
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![navigate_to])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

/// Navigate the webview to an external URL.
///
/// On Android, `window.location.href = url` is blocked by the system
/// WebView (shouldOverrideUrlLoading).  This command calls
/// `Webview::navigate()` which maps to `WebView.loadUrl()` and
/// bypasses that filter, allowing SSO redirects to work in-app.
#[tauri::command]
fn navigate_to(webview: tauri::Webview, url: String) -> Result<(), String> {
    webview
        .navigate(url.parse().map_err(|e: url::ParseError| e.to_string())?)
        .map_err(|e| e.to_string())
}
