# Frontend Usage Guide

## Prerequisites

- Node.js 18+
- Backend running at `http://localhost:8000` (see [blog-backend](https://github.com/vivek-modi-bot/blog-backend))
- Google OAuth configured on the backend

## Install & run

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### Optional env

Create `frontend/.env` if needed:

```env
VITE_API_URL=http://localhost:8000
```

Restart Vite after changing env vars.

## Using the app

1. **Browse** — Home lists posts; click a title to read.
2. **Sign in** — Log in / Sign up → Continue with Google.
3. **Write** — Write → title + rich editor → Publish.
4. **Manage** — My blogs, or Edit/Delete on your post page.
5. **Engage** — Like and comment (must be logged in).
6. **Profile** — Click your username → upload photo, save bio → View public profile.
7. **Authors** — Click any username/avatar to see their page and posts.

## Scripts

| Command | Purpose |
|---------|---------|
| `npm run dev` | Dev server |
| `npm run build` | Production build → `dist/` |
| `npm run preview` | Preview production build |
| `npm run lint` | Oxlint |

## Troubleshooting

| Issue | Fix |
|-------|-----|
| API errors / CORS | Ensure backend is on port 8000 and CORS allows `localhost:5173` |
| Login button missing | Backend `/api/auth/providers` must return `{ "google": true }` |
| Avatar not showing | Check network tab for `/uploads/avatars/...` on the API host |
| Empty editor publish | Editor must have real text (not only empty HTML tags) |
