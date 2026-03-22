# Add IBL.ai Profile Dropdown

Add a user profile dropdown with avatar, profile editing, tenant switching, and logout to this project.

## Prerequisites

- IBL.ai auth must already be integrated (run `/iblai-add-auth` first)

## Steps

### 1. Use MCP tools for documentation

- Call `get_component_info(componentName: "UserProfileDropdown")` for the full props reference
- Call `get_component_info(componentName: "Profile")` for the profile editor details

### 2. Import SDK styles

Add to your `globals.css` or root layout:
```css
@import "@iblai/iblai-js/web-containers/styles";
```

### 3. Create the profile dropdown wrapper

Create `components/iblai/profile-dropdown.tsx` that:
- Uses `UserProfileDropdown` from `@iblai/iblai-js/web-containers/next`
- Reads `username` and `tenantKey` from localStorage
- Wires up `handleLogout` and `redirectToAuthSpa` from the auth utils
- Configures which tabs/features to show (profile, account, tenant switcher, logout)

### 4. Place in your navbar

```tsx
import { IblaiProfileDropdown } from "@/components/iblai/profile-dropdown";

function Navbar() {
  return (
    <nav>
      {/* ... other nav items ... */}
      <IblaiProfileDropdown />
    </nav>
  );
}
```

### 5. Verify

Run `pnpm dev`, log in, and click the avatar to see the dropdown with profile editing.
