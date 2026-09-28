# Chronicles — Features

A blogging platform. FastAPI + SQLAlchemy (SQLite) backend, React (Vite) frontend.

## Authentication

- **Sign up with email (OTP, no password needed to verify)** — enter name/email/password, receive a 6-digit code by email, verify it to create the account. Code expires (`otp_expire_minutes`) and locks out after too many wrong attempts (`otp_max_attempts`).
- **Log in with email + password** — standard login, returns a JWT.
- **Continue with Google** — OAuth login/signup; no password is set for these accounts.
- **Forgot password** — request a reset code by email, enter it plus a new password, and you're auto-logged-in. Always returns the same generic message whether or not the email exists or has a password, so the endpoint can't be used to guess who has an account.
- **JWT sessions** — token stored in `localStorage`, sent as `Authorization: Bearer` on every request; `/api/auth/me` returns the current user.

## Profile

- **Edit bio and profile photo** (JPEG/PNG/WebP, 2MB max).
- **Public profile page** (`/users/:username`) showing bio, avatar, and that user's posts.
- **Set or change password** — every account can have a password, even ones created via Google:
  - No password yet → **"Set a password"** (new + confirm only).
  - Already has one → **"Change password"** (current + new + confirm, current is verified before the change).

## Blogging

- **Create, edit, delete** posts (title + content), only by their author.
- **Feed** of all posts and a **"My posts"** view.
- **Like / unlike** posts.
- **Comment** on posts, and delete your own comments.
- **Content moderation** — a word filter censors profanity/inappropriate terms in titles, bios, and comments before saving.

## Site Guide

- A small floating "Help" widget (bottom corner, all pages) with a static FAQ accordion (what is Chronicles, how to sign up/log in, how to post, like/comment, edit profile). No AI/backend calls — just local content.

## How it fits together

- **Backend** (`blog-backend/`): FastAPI routers — `auth.py` (signup/login/OAuth/password reset), `users.py` (profile, avatar, password), `blogs.py` (posts, likes, comments). SQLite via SQLAlchemy, tables auto-created on startup. Passwords and OTPs are hashed with bcrypt, never stored in plaintext.
- **Frontend** (`blog-frontend/`): React + React Router pages under `src/pages/`, a single `src/api.js` fetch wrapper, and a `useAuth()` context holding the logged-in user.
