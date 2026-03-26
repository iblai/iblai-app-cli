---
name: iblai-add-test
description: Write Playwright E2E journey tests for IBL.ai apps — auth flow, SDK components, mentor-ai web component, localStorage verification, multi-browser support
---

# Add Playwright Tests

Your app includes a full Playwright E2E test setup with SSO auth handling
and multi-browser support (Chromium, Firefox, WebKit).

## What's Already Set Up

```
e2e/
├── playwright.config.ts     # 3 browser setups (Chromium, Firefox, WebKit)
├── auth.setup.ts            # SSO auth — fills credentials, saves storage state per browser
├── .env.development         # APP_HOST, AUTH_HOST, PLAYWRIGHT_USERNAME/PASSWORD
├── custom-reporter.ts       # IBL.ai SDK reporter
└── journeys/
    ├── auth.journey.spec.ts # Auth flow + localStorage token verification
    └── chat.journey.spec.ts # ChatWidget + mentor-ai rendering
```

## Configure Credentials

Edit `e2e/.env.development`:

```bash
APP_HOST=http://localhost:3000
AUTH_HOST=https://auth.iblai.org
PLAYWRIGHT_USERNAME=your-email@example.com
PLAYWRIGHT_PASSWORD=your-password
AUTH_FLOW=username_password
```

## Run Tests

```bash
pnpm test:e2e                    # all browsers, headless
pnpm test:e2e:ui                 # interactive Playwright UI
pnpm test:e2e:headed             # all browsers, headed

# Single browser
npx playwright test --config e2e/playwright.config.ts --project=chromium

# Single test file
npx playwright test --config e2e/playwright.config.ts e2e/journeys/my-test.spec.ts

# Debug a specific test
npx playwright test --config e2e/playwright.config.ts --debug e2e/journeys/my-test.spec.ts
```

## How Auth Works in Tests

The `auth.setup.ts` runs before all journey tests and:

1. Navigates to `APP_HOST` → gets redirected to the auth SPA
2. Waits for URL containing `/login` and `app=agent`
3. Clicks "Continue with Password", fills credentials, submits
4. Waits for redirect back to `APP_HOST`
5. Waits for `axd_token` in localStorage
6. Saves browser storage state to `playwright/.auth/user-setup-{browser}.json`

Journey tests inherit this state automatically — **they start already logged in**.

## Write a New Journey Test

Create `e2e/journeys/my-feature.journey.spec.ts`:

```typescript
import { test, expect } from '@playwright/test';

test.describe('my feature journey', () => {
  test('page loads correctly', async ({ page }) => {
    const appHost = process.env.APP_HOST || 'http://localhost:3000';

    await page.goto(appHost + '/my-page');

    // Wait for content — all tokens are already in localStorage
    await expect(page.getByRole('heading', { name: 'My Page' })).toBeVisible({
      timeout: 10_000,
    });
  });
});
```

No login needed — the auth setup project already handled authentication.

---

## Common Test Patterns

### Verify page loads after auth

```typescript
test('authenticated user lands on home page', async ({ page }) => {
  const appHost = process.env.APP_HOST || 'http://localhost:3000';

  await page.goto(appHost);

  await page.waitForURL((url) => url.href.startsWith(appHost + '/'), {
    timeout: 15_000,
  });
  await expect(page).toHaveURL(new RegExp(`^${appHost}`));
});
```

### Verify auth tokens in localStorage

```typescript
test('auth tokens are stored in localStorage', async ({ page }) => {
  const appHost = process.env.APP_HOST || 'http://localhost:3000';

  await page.goto(appHost);
  await page.waitForLoadState('domcontentloaded', { timeout: 15_000 });

  // Wait for token (avoid networkidle — WebKit keeps WebSocket connections open)
  await page.waitForFunction(() => !!window.localStorage.getItem('axd_token'), {
    timeout: 10_000,
  });

  const token = await page.evaluate(() => window.localStorage.getItem('axd_token'));
  expect(token).toBeTruthy();

  const userData = await page.evaluate(() => window.localStorage.getItem('userData'));
  expect(userData).toBeTruthy();
  expect(JSON.parse(userData!)).toHaveProperty('user_nicename');
});
```

### Test an SDK component page (e.g., Profile)

```typescript
test('Profile component loads user data', async ({ page }) => {
  const appHost = process.env.APP_HOST || 'http://localhost:3000';

  await page.goto(appHost + '/profile');

  // Wait for the Profile component to render
  await expect(page.getByRole('heading', { name: 'Profile' })).toBeVisible({
    timeout: 15_000,
  });

  // Tabs are present
  await expect(page.getByRole('tab', { name: 'Basic' })).toBeVisible();
  await expect(page.getByRole('tab', { name: 'Social' })).toBeVisible();
});
```

### Test the mentor-ai web component

```typescript
test('ChatWidget renders mentor-ai web component', async ({ page }) => {
  const appHost = process.env.APP_HOST || 'http://localhost:3000';

  await page.goto(appHost);

  // mentor-ai takes time to dynamically load
  const chatWidget = page.locator('mentor-ai');
  await expect(chatWidget).toBeVisible({ timeout: 30_000 });

  // Verify key attributes
  await expect(chatWidget).toHaveAttribute('authrelyonhost', 'true');
  await expect(chatWidget).toHaveAttribute('extraparams', 'hide-navbar=1');
});
```

### Access the mentor-ai shadow DOM (iframe)

```typescript
test('mentor-ai iframe loads', async ({ page }) => {
  const appHost = process.env.APP_HOST || 'http://localhost:3000';

  await page.goto(appHost);
  await page.waitForSelector('mentor-ai', { timeout: 30_000 });

  // The web component renders an iframe inside its Shadow DOM
  const iframe = await page.evaluateHandle(() => {
    const el = document.querySelector('mentor-ai');
    return el?.shadowRoot?.querySelector('iframe') ?? null;
  });

  expect(iframe).not.toBeNull();
});
```

### Verify an API call succeeds

```typescript
test('user metadata API returns 200', async ({ page }) => {
  const appHost = process.env.APP_HOST || 'http://localhost:3000';

  const responsePromise = page.waitForResponse(
    (resp) =>
      resp.url().includes('/api/ibl/users/manage/metadata') &&
      resp.status() === 200,
  );

  await page.goto(appHost + '/profile');
  const response = await responsePromise;
  expect(response.status()).toBe(200);
});
```

### Test form fields

```typescript
test('profile fields are editable', async ({ page }) => {
  const appHost = process.env.APP_HOST || 'http://localhost:3000';

  await page.goto(appHost + '/profile');

  const fullName = page.getByLabel('Full Name');
  await expect(fullName).toBeVisible({ timeout: 15_000 });

  await fullName.fill('Test User');
  await expect(fullName).toHaveValue('Test User');
});
```

### Navigate between pages

```typescript
test('can navigate to profile from home', async ({ page }) => {
  const appHost = process.env.APP_HOST || 'http://localhost:3000';

  await page.goto(appHost);
  await page.getByRole('link', { name: /profile/i }).click();
  await expect(page).toHaveURL(appHost + '/profile');
});
```

---

## Tips & Gotchas

| Issue | Solution |
|-------|----------|
| WebKit `networkidle` timeout | Use `domcontentloaded` + `waitForFunction` for a specific token instead |
| mentor-ai takes 20-30s | Use `{ timeout: 30_000 }` on `toBeVisible()` for chat widget tests |
| Shadow DOM access | Use `page.evaluateHandle(() => el.shadowRoot.querySelector(...))` |
| Stale auth state | Delete `playwright/.auth/*.json` and re-run setup |
| SDK component empty data | Check console errors — `initializeDataLayer` may not have been called |
| Screenshot on failure | Automatically saved to `test-results/` — check there first |
| Trace on retry | Captured on first retry — view with `npx playwright show-trace <trace-file>` |
