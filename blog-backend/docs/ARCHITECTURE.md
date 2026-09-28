# Backend Architecture

## Stack

- **FastAPI** + **Uvicorn**
- **SQLAlchemy 2** + **SQLite** (`blog.db`)
- **Google OAuth 2.0** (authorization code) → app **JWT** (`python-jose`)
- Static files under `/uploads` for avatars

## Package layout

```text
backend/
├── app/
│   ├── main.py           # App, CORS, schema migrate, StaticFiles
│   ├── config.py         # pydantic-settings from .env
│   ├── database.py       # Engine + SessionLocal
│   ├── models.py         # User, Blog, Like, Comment
│   ├── schemas.py        # Request/response DTOs
│   ├── auth.py           # JWT + get_current_user(_optional)
│   ├── paths.py          # UPLOAD_ROOT / AVATAR_DIR
│   └── routers/
│       ├── auth.py       # Google OAuth + /me
│       ├── blogs.py      # CRUD, likes, comments
│       └── users.py      # Profile, avatar, public users
├── uploads/avatars/      # Served at /uploads/avatars/*
├── .env.example
├── requirements.txt
└── blog.db               # Local DB (gitignored)
```

## Data model

```text
User ──< Blog
User ──< Like >── Blog     (unique per user+blog)
User ──< Comment >── Blog
```

| Table | Notable columns |
|-------|-----------------|
| `users` | `username`, `email`, `oauth_*`, `bio`, `avatar_url` |
| `blogs` | `title`, `content` (HTML), `author_id`, timestamps |
| `likes` | `user_id`, `blog_id` |
| `comments` | `content`, `user_id`, `blog_id` |

## Auth

1. `GET /api/auth/google` → redirect to Google  
2. Callback exchanges `code`, upserts `User`, issues JWT (`sub` = username)  
3. Redirect to `{FRONTEND_URL}/auth/callback?token=...`  
4. Protected routes use `Authorization: Bearer <token>`  
5. Optional auth on public blog reads sets `liked_by_me`

## Ownership rules

- Blog update/delete: author only  
- Like / comment create: any authenticated user  
- Comment delete: comment author **or** blog author  

## Uploads

- `POST /api/users/me/avatar` writes to `backend/uploads/avatars/`  
- `avatar_url` stored as `/uploads/avatars/<file>`  
- `StaticFiles` mounts `UPLOAD_ROOT` at `/uploads`  
- Allowed: JPEG, PNG, WebP ≤ 2MB  

## Config (`.env`)

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | JWT + OAuth state signing |
| `BACKEND_URL` | e.g. `http://localhost:8000` (OAuth redirect base) |
| `FRONTEND_URL` | e.g. `http://localhost:5173` (post-login redirect) |
| `GOOGLE_CLIENT_ID` | Google OAuth client |
| `GOOGLE_CLIENT_SECRET` | Google OAuth secret |
