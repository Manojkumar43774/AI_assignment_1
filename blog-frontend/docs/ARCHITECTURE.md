# Frontend Architecture

## Stack

- **React 19** + **Vite 8**
- **React Router** for client-side routing
- **TipTap** rich text editor for blog bodies
- **DOMPurify** to sanitize HTML before render
- API client in `src/api.js` (Bearer JWT from `localStorage`)

## Folder layout

```text
frontend/src/
├── api.js                 # HTTP client → backend
├── AuthContext.jsx        # Session (token → /api/auth/me)
├── App.jsx                # Route table
├── main.jsx
├── index.css
├── components/
│   ├── Navbar.jsx
│   ├── Avatar.jsx         # Avatar + mediaUrl + sanitizeHtml
│   └── RichTextEditor.jsx # TipTap toolbar + editor
└── pages/
    ├── Home.jsx           # Public feed
    ├── PostDetail.jsx     # Read, like, comment, owner actions
    ├── NewBlog.jsx        # Create post
    ├── EditBlog.jsx       # Edit own post
    ├── MyBlogs.jsx        # Manage own posts
    ├── Profile.jsx        # Edit bio + upload avatar
    ├── UserProfile.jsx    # Public author page
    ├── Login.jsx / Register.jsx
    └── AuthCallback.jsx   # OAuth return → store JWT
```

## Routes

| Path | Auth | Purpose |
|------|------|---------|
| `/` | Public | Latest posts |
| `/posts/:id` | Public | Post detail, likes, comments |
| `/posts/:id/edit` | Owner | Edit with TipTap |
| `/new` | Logged in | Create post |
| `/my-blogs` | Logged in | List / delete own posts |
| `/profile` | Logged in | Bio + photo |
| `/users/:username` | Public | Author profile + their blogs |
| `/login`, `/register` | Public | Start Google OAuth |
| `/auth/callback` | Public | Save `?token=` after Google redirect |

## Auth data flow

```text
Login button → GET {API}/api/auth/google
  → Google consent
  → Backend callback
  → Redirect /auth/callback?token=JWT
  → localStorage.token = JWT
  → GET /api/auth/me → AuthContext.user
  → All api.* calls send Authorization: Bearer <token>
```

## Key UI behaviors

- Guests can browse feed, posts, and public profiles.
- TipTap stores **HTML** in `content`; PostDetail renders via `sanitizeHtml`.
- Avatar URLs like `/uploads/avatars/...` are prefixed with `VITE_API_URL` / `http://localhost:8000`.
- Owner-only Edit/Delete appear when `user.id === blog.author_id`.

## Config

| Variable | Default | Meaning |
|----------|---------|---------|
| `VITE_API_URL` | `http://localhost:8000` | Backend base URL |
