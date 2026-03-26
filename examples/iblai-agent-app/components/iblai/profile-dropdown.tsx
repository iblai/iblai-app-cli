"use client";

/**
 * IBL.ai Profile Dropdown
 *
 * A fully self-contained user avatar + dropdown menu with profile editing,
 * tenant switching, and logout. Uses the SDK's UserProfileDropdown component.
 *
 * Usage:
 *   import { ProfileDropdown } from "@/components/iblai/profile-dropdown";
 *   <ProfileDropdown />
 *
 * Prerequisites:
 *   - <IblaiProviders> must wrap this component's ancestor tree
 *   - @iblai/iblai-js/web-containers/styles must be imported in globals.css
 */

import { useMemo } from "react";
import { UserProfileDropdown } from "@iblai/iblai-js/web-containers/next";
import config from "@/lib/iblai/config";
import { handleLogout, redirectToAuthSpa } from "@/lib/iblai/auth-utils";

interface ProfileDropdownProps {
  /** Additional CSS class for the dropdown trigger. */
  className?: string;
}

export function ProfileDropdown({ className }: ProfileDropdownProps) {
  const username = useMemo(() => {
    if (typeof window === "undefined") return "";
    try {
      const raw = localStorage.getItem("userData");
      return raw ? JSON.parse(raw).user_nicename ?? "" : "";
    } catch {
      return "";
    }
  }, []);

  const tenantKey = useMemo(() => {
    if (typeof window === "undefined") return "";
    return localStorage.getItem("tenant") ?? "";
  }, []);

  return (
    <UserProfileDropdown
      username={username}
      tenantKey={tenantKey}
      userIsAdmin={false}
      showProfileTab
      showAccountTab={false}
      showTenantSwitcher={false}
      showHelpLink={false}
      showLogoutButton
      authURL={config.authUrl()}
      onLogout={handleLogout}
      onTenantChange={(tenant: string) => {
        localStorage.setItem("tenant", tenant);
        redirectToAuthSpa(undefined, tenant, true, true);
      }}
      onTenantUpdate={(tenant: any) => {
        if (tenant?.key) localStorage.setItem("tenant", tenant.key);
      }}
      className={className}
    />
  );
}
