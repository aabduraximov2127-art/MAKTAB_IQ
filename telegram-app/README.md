# MaktabIQ — Telegram Mini App

A small, standalone React app that runs *inside* Telegram (as a "Mini App" / WebApp) and
shows a compact, role-aware home screen: today's lessons, latest grades, homework,
unread notifications — pulled from the same Django REST API the main site (`../frontend/`)
uses. It's deliberately separate from `frontend/`: a Mini App needs to load fast on mobile
inside Telegram's webview, so it doesn't drag in the full admin site's router/sidebar/chart
stack.

## How sign-in works — no password needed after the first time

Telegram hands every Mini App a signed `initData` string proving which Telegram account
opened it (signed with the bot token, so only Telegram could have produced it). This app
uses that instead of a login screen, most of the time:

1. **Already linked** (this Telegram chat is bound to a MaktabIQ account, e.g. via the
   website's "Yordam" → Telegram code, or via step 2 below): `POST /api/v1/auth/telegram/`
   with the initData → backend verifies the signature, finds the linked account, returns a
   JWT. Straight to the home screen, no form.
2. **First time**: the backend replies "not linked yet" → this app shows a small
   username/password form → `POST /api/v1/auth/telegram/login/` verifies *both* the
   initData signature *and* the password, links the chat, returns a JWT. Every later open
   is then case 1.

See `apps/users/telegram_webapp.py` (signature verification) and
`apps/users/telegram_link.py` (linking) in the backend for the actual logic — this app is
just a thin client over those two endpoints plus the ordinary REST API (`/lessons/`,
`/grades/`, `/analytics/...`, `/notifications/...`), reusing exactly the same per-role
scoping the main site's Dashboard relies on.

## Running it locally

```bash
cd telegram-app
npm install
npm run dev        # http://localhost:5174, proxies /api to the Django backend on :8000
```

Opening `http://localhost:5174` directly in a normal browser tab (not inside Telegram)
works too, for iterating on layout/styling — `src/telegram.ts` installs a small stand-in
for `window.Telegram.WebApp` in dev mode so the app renders instead of erroring. That
stand-in's `initData` is empty on purpose (there's no real Telegram signing it), so actual
sign-in only completes once the app is genuinely opened through Telegram.

## Trying it for real inside Telegram

Telegram only opens Mini App buttons over **HTTPS**, so `localhost` alone isn't reachable
from the Telegram client. For local development, expose the dev server through a tunnel:

```bash
npx localtunnel --port 5174        # or: npx cloudflared tunnel --url http://localhost:5174
```

That prints an `https://...` URL. Put it in the project's `.env` as `TELEGRAM_WEBAPP_URL`
and restart the bot (`python -m bot.bot`) — it sets the chat's menu button and the `/app`
command's button to that URL on startup. Open a chat with the bot in Telegram and tap the
menu button (or send `/app`).

For a real deployment, build the app (`npm run build` → `dist/`), serve those static files
over HTTPS from your own domain (same idea as deploying `frontend/`'s build — any static
host or a simple nginx container works), and point `TELEGRAM_WEBAPP_URL` at that instead of
a tunnel.

### Optional: "open full site" link

Set `VITE_FULL_SITE_URL` (see `.env.example`) to the desktop site's URL to show a
"To'liq saytni ochish" link in the footer. Leave it unset to hide that link.

## Notes

- Sessions live in `sessionStorage` (cleared when the Telegram webview closes) — reopening
  the Mini App just re-authenticates via `initData`, so this is fine.
- "Telegramdan uzish" in the footer unlinks the chat (`POST /users/me/telegram-unlink/`)
  and drops back to the login screen; reopening later shows the login form again.
- Colors come entirely from Telegram's own `--tg-theme-*` CSS variables (`src/styles.css`),
  so the app automatically matches whatever light/dark theme the user's Telegram client is
  using — it does not use the main site's own color scheme.
