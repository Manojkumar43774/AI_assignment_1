# Blog Backend

FastAPI API for Ink & Co. — Google OAuth2, blogs, likes, comments, profiles.

## Documentation

All docs live in **[`docs/`](docs/)**:

| Doc | Description |
|-----|-------------|
| [docs/README.md](docs/README.md) | Docs index |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Backend architecture |
| [docs/API.md](docs/API.md) | API contracts |
| [docs/USAGE.md](docs/USAGE.md) | Setup & usage |
| [docs/TECHNICAL_DOCUMENTATION.md](docs/TECHNICAL_DOCUMENTATION.md) | Full system documentation |

Frontend: https://github.com/vivek-modi-bot/blog-frontend

## Quick start

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs  
Redirect URI: `http://localhost:8000/api/auth/google/callback`
