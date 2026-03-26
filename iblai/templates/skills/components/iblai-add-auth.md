# Add IBL.ai Authentication

Add SSO authentication from IBL.ai to this Next.js project. After completion, unauthenticated users will be redirected to the IBL Auth SPA, and tokens will be stored in localStorage on return.

## Prerequisites

- Next.js 13+ with App Router
- npm/pnpm package manager

## Steps

### 1. Analyze the project

- Read `package.json` to check for existing `@iblai/iblai-js`, `@reduxjs/toolkit`, `react-redux`
- Read the root layout (`app/layout.tsx`) to understand the current provider structure
- Check if a Redux store already exists

### 2. Install dependencies

```bash
pnpm add @iblai/iblai-js @reduxjs/toolkit react-redux
```

### 3. Use MCP tools for documentation

- Call `get_provider_setup(appType: "auth")` to get the correct provider hierarchy
- Call `get_component_info(componentName: "SsoLogin")` for the SSO callback component

### 4. Create configuration files

Create `lib/iblai/config.ts` with environment variable accessors for `NEXT_PUBLIC_AUTH_URL`, `NEXT_PUBLIC_DM_URL`, `NEXT_PUBLIC_LMS_URL`.

Create `lib/iblai/storage-service.ts` implementing the `StorageService` interface with localStorage.

Create `lib/iblai/auth-utils.ts` with `redirectToAuthSpa()`, `hasNonExpiredAuthToken()`, and `handleLogout()`.

### 5. Create SSO callback route

Create `app/sso-login-complete/page.tsx` using the `SsoLogin` component from `@iblai/iblai-js/web-containers/next`.

### 6. Create Redux store

Create `store/iblai-store.ts` with `coreApiSlice`, `mentorReducer`, `mentorMiddleware`, `chatSliceReducerShared`, and `filesReducer`.

### 7. Create providers wrapper

Create `providers/iblai-providers.tsx` that wraps `ReduxProvider` > `AuthProvider` > `TenantProvider`. Call `initializeDataLayer()` on mount.

### 8. Wire into existing layout

Wrap the root layout's `{children}` with `<IblaiProviders>`.

### 9. Add environment variables

Add to `.env.local`:
```
NEXT_PUBLIC_AUTH_URL=https://auth.iblai.org
NEXT_PUBLIC_DM_URL=https://base.manager.iblai.app
NEXT_PUBLIC_LMS_URL=https://learn.iblai.app
```

### 10. Verify

Run `pnpm dev`. The app should redirect to the IBL Auth SPA for login. After authenticating, the user should be redirected back to the app.
