from pathlib import Path

# backend/uploads — shared by upload routes and StaticFiles mount
UPLOAD_ROOT = Path(__file__).resolve().parent.parent / "uploads"
AVATAR_DIR = UPLOAD_ROOT / "avatars"
