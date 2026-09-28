# Ink & Co. — Technical Documentation

System architecture, API contracts, and usage guide for the blog platform.

| Item | Value |
|------|--------|
| Frontend | React 19 + Vite (`frontend/`) |
| Backend | FastAPI + SQLAlchemy + SQLite (`backend/`) |
| Auth | Google OAuth 2.0 (authorization code) → app JWT |
| Default URLs | App `http://localhost:5173` · API `http://localhost:8000` |

---

## 1. System Architecture

### 1.1 High-level view

```text
┌─────────────────────┐         HTTPS / JSON          ┌──────────────────────┐
│  React + Vite SPA   │ ─────────────────────────────▶│  FastAPI (Uvicorn)   │
│  localhost:5173     │◀──── JWT Bearer + JSON ───────│  localhost:8000      │
└─────────┬───────────┘                               └──────────┬───────────┘
          │                                                      │
          │ Google OAuth redirect                                │
          │ (browser leaves SPA)                                 ▼
          │                                           ┌──────────────────────┐
          │                                           │  SQLite (blog.db)    │
          │                                           │  users, blogs, likes │
          │                                           │  comments            │
          │                                           └──────────────────────┘
          │                                                      │
          ▼                                                      ▼
┌─────────────────────┐                               ┌──────────────────────┐
│  Google Accounts    │◀── OAuth code exchange ───────│  Static uploads/     │
│  (identity provider)│                               │  avatars/*.jpg|png   │
└─────────────────────┘                               └──────────────────────┘
```

### 1.2 Design principles

- **Public read, authenticated write** — anyone can list/read posts and profiles; mutations require a JWT.
- **User-owned content** — only the author can edit/delete their blogs; comment authors (or the post author) can delete comments.
- **OAuth for identity** — no local passwords; Google issues identity, the API issues a short-lived JWT for the SPA.
- **Rich content as HTML** — TipTap produces HTML; the API stores it; the SPA sanitizes with DOMPurify before render.

### 1.3 Component map

#### Backend (`backend/app/`)

| Module | Responsibility |
|--------|----------------|
| `main.py` | App factory, CORS, schema bootstrap, static `/uploads` mount |
| `config.py` | Env settings (`GOOGLE_*`, URLs, `SECRET_KEY`) |
| `database.py` | SQLAlchemy engine + session |
| `models.py` | `User`, `Blog`, `Like`, `Comment` |
| `schemas.py` | Pydantic request/response contracts |
| `auth.py` | JWT create/verify, optional + required current user |
| `paths.py` | Shared upload directory roots |
| `routers/auth.py` | Google OAuth start/callback, `/me`, providers |
| `routers/blogs.py` | CRUD blogs, likes, comments |
| `routers/users.py` | Profile update, avatar upload, public profiles |

#### Frontend (`frontend/src/`)

| Area | Responsibility |
|------|----------------|
| `api.js` | HTTP client (Bearer token, FormData uploads) |
| `AuthContext.jsx` | Session bootstrap from `localStorage` token |
| `pages/*` | Routes: home, post, editor, profile, OAuth callback |
| `components/RichTextEditor.jsx` | TipTap editor for post body |
| `components/Avatar.jsx` | Avatar + `mediaUrl` / `sanitizeHtml` helpers |

### 1.4 Data model

```text
User 1───* Blog
User 1───* Like
User 1───* Comment
Blog 1───* Like      (unique user_id + blog_id)
Blog 1───* Comment
```

| Entity | Key fields |
|--------|------------|
| **User** | `username`, `email`, `oauth_provider`, `oauth_id`, `bio`, `avatar_url` |
| **Blog** | `title`, `content` (HTML), `author_id`, `created_at`, `updated_at` |
| **Like** | `user_id`, `blog_id` |
| **Comment** | `content` (plain text), `user_id`, `blog_id`, `created_at` |

### 1.5 Auth flow

```text
1. SPA → GET /api/auth/google
2. API redirects → Google consent screen
3. Google → GET /api/auth/google/callback?code&state
4. API exchanges code, upserts User, mints JWT
5. API redirects → FRONTEND_URL/auth/callback?token=...
6. SPA stores token in localStorage, calls GET /api/auth/me
7. Subsequent API calls send: Authorization: Bearer <jwt>
```

JWT payload includes `sub` (username) and `exp` (default 24h). State is a short-lived signed JWT binding the OAuth provider.

### 1.6 Request authorization matrix

| Action | Guest | Logged-in user | Post author |
|--------|-------|----------------|-------------|
| List / read blogs | ✓ | ✓ | ✓ |
| View public profile | ✓ | ✓ | ✓ |
| Create / edit / delete own blog | | ✓ (own) | ✓ |
| Like / unlike | | ✓ | ✓ |
| Comment | | ✓ | ✓ |
| Delete comment | | own comment | any on their post |
| Update bio / avatar | | self | |

---

## 2. API Contracts

Base URL: `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`  
Auth header (protected routes): `Authorization: Bearer <access_token>`

Unless noted, request/response bodies are `application/json`.  
Avatar upload uses `multipart/form-data`.

### 2.1 Health

#### `GET /api/health`

**Auth:** none  

**Response `200`**
```json
{ "status": "ok" }
```

---

### 2.2 Auth

#### `GET /api/auth/providers`

**Auth:** none  

**Response `200`**
```json
{ "google": true }
```

#### `GET /api/auth/google`

**Auth:** none  
**Behavior:** `302` redirect to Google OAuth.  
**Errors:** `503` if `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` missing.

#### `GET /api/auth/google/callback`

**Auth:** none (browser redirect from Google)  
**Query:** `code`, `state` (required); `error` optional  
**Behavior:** upserts user, then `302` to `{FRONTEND_URL}/auth/callback?token=<jwt>`

#### `GET /api/auth/me`

**Auth:** required  

**Response `200` — UserOut**
```json
{
  "id": 1,
  "username": "VivekModi",
  "email": "user@example.com",
  "bio": "Writer and builder.",
  "avatar_url": "/uploads/avatars/1_abc.png"
}
```

---

### 2.3 Blogs

#### BlogOut (shared shape)

```json
{
  "id": 1,
  "title": "Hello",
  "content": "<p>Rich HTML from TipTap</p>",
  "author_id": 1,
  "author_username": "VivekModi",
  "author_avatar_url": "/uploads/avatars/1_abc.png",
  "created_at": "2026-09-24T10:00:00",
  "updated_at": "2026-09-24T11:00:00",
  "like_count": 3,
  "comment_count": 2,
  "liked_by_me": false
}
```

`liked_by_me` is `true` only when a valid Bearer token is sent and that user has liked the post.

#### `GET /api/blogs`

**Auth:** optional  
**Response `200`:** `BlogOut[]` (newest first)

#### `GET /api/blogs/mine`

**Auth:** required  
**Response `200`:** `BlogOut[]` for the current user

#### `GET /api/blogs/{blog_id}`

**Auth:** optional  
**Response `200`:** `BlogOut`  
**Errors:** `404` not found

#### `POST /api/blogs`

**Auth:** required  

**Request**
```json
{
  "title": "My post",
  "content": "<p>Body HTML</p>"
}
```

**Response `201`:** `BlogOut`

#### `PUT /api/blogs/{blog_id}`

**Auth:** required (author only)  

**Request:** same as create  
**Response `200`:** `BlogOut`  
**Errors:** `403` not owner · `404` not found

#### `DELETE /api/blogs/{blog_id}`

**Auth:** required (author only)  
**Response `204`:** empty  
**Errors:** `403` · `404`

#### `POST /api/blogs/{blog_id}/like`

**Auth:** required  
**Behavior:** toggles like  

**Response `200`**
```json
{ "liked": true, "like_count": 4 }
```

#### `GET /api/blogs/{blog_id}/comments`

**Auth:** none  

**Response `200` — CommentOut[]**
```json
[
  {
    "id": 1,
    "content": "Nice post!",
    "user_id": 2,
    "username": "reader1",
    "avatar_url": null,
    "blog_id": 1,
    "created_at": "2026-09-24T12:00:00"
  }
]
```

#### `POST /api/blogs/{blog_id}/comments`

**Auth:** required  

**Request**
```json
{ "content": "Nice post!" }
```

**Response `201`:** `CommentOut`

#### `DELETE /api/blogs/{blog_id}/comments/{comment_id}`

**Auth:** required (comment author **or** post author)  
**Response `204`:** empty  
**Errors:** `403` · `404`

---

### 2.4 Users & profiles

#### `GET /api/users/{username}`

**Auth:** none  

**Response `200` — PublicUserOut**
```json
{
  "id": 1,
  "username": "VivekModi",
  "bio": "Writer and builder.",
  "avatar_url": "/uploads/avatars/1_abc.png",
  "blog_count": 5,
  "created_at": "2026-09-24T09:00:00"
}
```

#### `GET /api/users/{username}/blogs`

**Auth:** none  
**Response `200`:** `BlogOut[]` for that user

#### `PATCH /api/users/me`

**Auth:** required  

**Request**
```json
{ "bio": "Updated bio (max 500 chars)" }
```

**Response `200`:** `UserOut`

#### `POST /api/users/me/avatar`

**Auth:** required  
**Content-Type:** `multipart/form-data`  
**Field:** `file` — JPEG, PNG, or WebP, max 2MB  

**Response `200`:** `UserOut` with updated `avatar_url`  
**Static URL:** `GET http://localhost:8000{avatar_url}`

---

### 2.5 Error shape

```json
{ "detail": "Human-readable message" }
```

Validation errors may return `detail` as an array of `{ "loc", "msg", "type" }` objects (FastAPI/Pydantic default).

| Status | Typical meaning |
|--------|-----------------|
| `400` | Bad input (OAuth, file type/size) |
| `401` | Missing/invalid JWT |
| `403` | Authenticated but not allowed |
| `404` | Resource missing |
| `503` | Google OAuth not configured |

---

### 2.6 Frontend routes (SPA)

| Path | Access | Purpose |
|------|--------|---------|
| `/` | Public | Feed |
| `/posts/:id` | Public | Read post, likes, comments |
| `/posts/:id/edit` | Auth + owner | Edit with TipTap |
| `/new` | Auth | Create post |
| `/my-blogs` | Auth | Manage own posts |
| `/profile` | Auth | Bio + avatar |
| `/users/:username` | Public | Author profile + their posts |
| `/login`, `/register` | Public | Google OAuth entry |
| `/auth/callback` | Public | Persist token after OAuth |

---

## 3. Usage Guide

### 3.1 Prerequisites

- Node.js 18+ and npm  
- Python 3.11+ (3.13 tested)  
- Google Cloud OAuth 2.0 **Web** client  

### 3.2 Configure Google OAuth

1. [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials)
2. Create **OAuth client ID** → Application type **Web application**
3. Authorized JavaScript origins: `http://localhost:5173`
4. Authorized redirect URI: `http://localhost:8000/api/auth/google/callback`
5. While the consent screen is in **Testing**, add your Google account under **Test users**
6. Copy client ID and secret into `backend/.env`:

```env
SECRET_KEY=dev-secret-change-me-in-production
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173
GOOGLE_CLIENT_ID=....apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-...
```

Use `backend/.env.example` as a template. **Never commit `.env`.**

### 3.3 Start the backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- API: http://localhost:8000  
- Swagger UI: http://localhost:8000/docs  
- SQLite file: `backend/blog.db` (created automatically)  
- Avatars: `backend/uploads/avatars/`

### 3.4 Start the frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173  

Optional: `VITE_API_URL=http://localhost:8000` if the API host differs.

### 3.5 End-user walkthrough

1. **Browse as guest** — open the home page; open any post; open an author name to see their profile and posts.
2. **Sign in** — Log in / Sign up → **Continue with Google** → return to the app signed in.
3. **Write** — Write → compose title + rich text → Publish.
4. **Manage** — My blogs → Edit / Delete; or Edit/Delete from the post page if you are the author.
5. **Engage** — Like a post; leave a comment (login required).
6. **Profile** — Click your username in the nav → upload photo + save bio → **View public profile**.

### 3.6 Developer tips

- After changing `.env`, restart Uvicorn (settings load at process start).
- Interactive API exploration: http://localhost:8000/docs (use **Authorize** with a JWT from `/auth/callback?token=`).
- Separate GitHub repos (if used): `blog-frontend`, `blog-backend` — keep secrets out of git.
- CORS allows only `http://localhost:5173` and `http://127.0.0.1:5173` by default.

### 3.7 Troubleshooting

| Symptom | Likely fix |
|---------|------------|
| Login shows “OAuth not configured” | Fill `GOOGLE_*` in `.env` and restart API |
| Google “access blocked” / 403 | Add yourself as OAuth **Test user** |
| Redirect URI mismatch | Must be exactly `http://localhost:8000/api/auth/google/callback` |
| Avatar upload OK but image broken | Confirm file exists under `backend/uploads/avatars/` and API is serving `/uploads` |
| `401` on write actions | Sign in again; token may be expired or missing |
| `403` on edit/delete | Only the post author can manage that post |

---

## 4. Repository layout

```text
00-blog-site/
├── docs/
│   └── TECHNICAL_DOCUMENTATION.md   ← this file
├── README.md
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── auth.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── paths.py
│   │   └── routers/
│   │       ├── auth.py
│   │       ├── blogs.py
│   │       └── users.py
│   ├── uploads/avatars/
│   ├── .env.example
│   ├── requirements.txt
│   └── blog.db                      # local only; gitignored
└── frontend/
    ├── src/
    │   ├── api.js
    │   ├── AuthContext.jsx
    │   ├── App.jsx
    │   ├── components/
    │   └── pages/
    └── package.json
```

---

*Generated for the Ink & Co. blog platform — React + FastAPI.*
