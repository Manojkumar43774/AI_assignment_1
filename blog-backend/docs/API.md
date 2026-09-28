# Backend API Contracts

Base URL: `http://localhost:8000`  
Auth: `Authorization: Bearer <jwt>` where required.

## Health

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| GET | `/api/health` | No | `{ "status": "ok" }` |

## Auth

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| GET | `/api/auth/providers` | No | `{ "google": true\|false }` |
| GET | `/api/auth/google` | No | 302 → Google |
| GET | `/api/auth/google/callback` | No | 302 → frontend with `token` |
| GET | `/api/auth/me` | Yes | Current `UserOut` |

### UserOut

```json
{
  "id": 1,
  "username": "VivekModi",
  "email": "user@example.com",
  "bio": "…",
  "avatar_url": "/uploads/avatars/1_….png"
}
```

## Blogs

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| GET | `/api/blogs` | Optional | List `BlogOut[]` |
| GET | `/api/blogs/mine` | Yes | Current user’s blogs |
| GET | `/api/blogs/{id}` | Optional | One blog |
| POST | `/api/blogs` | Yes | Create `{ title, content }` → 201 |
| PUT | `/api/blogs/{id}` | Yes (owner) | Update |
| DELETE | `/api/blogs/{id}` | Yes (owner) | 204 |
| POST | `/api/blogs/{id}/like` | Yes | Toggle → `{ liked, like_count }` |
| GET | `/api/blogs/{id}/comments` | No | `CommentOut[]` |
| POST | `/api/blogs/{id}/comments` | Yes | `{ content }` → 201 |
| DELETE | `/api/blogs/{id}/comments/{cid}` | Yes* | 204 (*author or post owner) |

### BlogOut

```json
{
  "id": 1,
  "title": "Hello",
  "content": "<p>HTML</p>",
  "author_id": 1,
  "author_username": "VivekModi",
  "author_avatar_url": "/uploads/avatars/…",
  "created_at": "…",
  "updated_at": "…",
  "like_count": 0,
  "comment_count": 0,
  "liked_by_me": false
}
```

## Users

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| GET | `/api/users/{username}` | No | Public profile |
| GET | `/api/users/{username}/blogs` | No | That user’s blogs |
| PATCH | `/api/users/me` | Yes | `{ "bio": "…" }` |
| POST | `/api/users/me/avatar` | Yes | `multipart/form-data` field `file` |

### Errors

```json
{ "detail": "message" }
```

Common: `400` bad input · `401` unauthorized · `403` forbidden · `404` missing · `503` OAuth not configured

Interactive explorer: http://localhost:8000/docs
