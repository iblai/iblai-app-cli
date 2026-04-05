import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { config } from "./config";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Redirect to the Auth SPA for login/logout
 */
export async function redirectToAuthSpa(
  redirectTo?: string,
  platformKey?: string,
  logout?: boolean,
  saveRedirect = true
): Promise<void> {
  const AUTH_URL = config.authUrl();
  const AGENT_URL = config.agentUrl();

  // Clear local storage on logout
  if (logout) {
    localStorage.clear();
  }

  // Save redirect path
  if (saveRedirect && !logout) {
    const currentPath = window.location.pathname + window.location.search;
    localStorage.setItem("redirect_to", currentPath);
  }

  // Build auth URL with parameters
  const params = new URLSearchParams({
    app: "agent",
    "redirect-to": redirectTo || AGENT_URL,
  });

  if (platformKey) {
    params.set("tenant", platformKey);
  }

  if (logout) {
    params.set("logout", "true");
  }

  const authUrl = `${AUTH_URL}/login?${params.toString()}`;

  // On Tauri mobile, window.location.href is blocked by the Android WebView
  // for external URLs. Use the navigate_to command to bypass the filter.
  if (typeof window !== "undefined" && "__TAURI__" in window) {
    const { invoke } = await import("@tauri-apps/api/core");
    try {
      await invoke("navigate_to", { url: authUrl });
      return;
    } catch { /* fall through */ }
  }
  window.location.href = authUrl;
}