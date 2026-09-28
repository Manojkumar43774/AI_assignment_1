# Backend Usage Guide

## Prerequisites

- Python 3.11+
- Google Cloud OAuth 2.0 **Web** client

## Google OAuth setup

1. [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials)
2. Create OAuth client → **Web application**
3. JavaScript origin: `http://localhost:5173`
4. Redirect URI: `http://localhost:8000/api/auth/google/callback`
5. Add your Google account as a **Test user** if the app is in Testing
6. Copy ID + secret into `.env`

```bash
cp .env.example .env
```

```env
SECRET_KEY=dev-secret-change-me-in-production
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173
GOOGLE_CLIENT_ID=....apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-...
```

**Do not commit `.env`.**

## Install & run

```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- API: http://localhost:8000  
- Swagger: http://localhost:8000/docs  
- DB: `blog.db` (auto-created)  
- Avatars: `uploads/avatars/`

Restart Uvicorn after editing `.env`.

## Smoke checks

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/auth/providers
curl http://localhost:8000/api/blogs
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `google: false` / 503 on login | Set `GOOGLE_*` and restart |
| Redirect URI mismatch | Exact match: `http://localhost:8000/api/auth/google/callback` |
| Google access blocked | Add Test user on consent screen |
| Avatar 404 | Files must live in `backend/uploads/avatars/` (not `app/uploads`) |
| 401 on protected routes | Send valid Bearer JWT from OAuth callback |

## Related

- Frontend: [blog-frontend](https://github.com/vivek-modi-bot/blog-frontend)  
- Docs index: [README.md](./README.md)
