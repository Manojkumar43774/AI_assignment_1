import DOMPurify from "dompurify";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function mediaUrl(path) {
  if (!path) return null;
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  return `${API_URL}${path}`;
}

export function sanitizeHtml(html) {
  return DOMPurify.sanitize(html || "", {
    USE_PROFILES: { html: true },
  });
}

export default function Avatar({ src, name, size = 40 }) {
  const url = mediaUrl(src);
  const initials = (name || "?").slice(0, 1).toUpperCase();

  if (url) {
    return (
      <img
        className="avatar"
        src={url}
        alt={name || "avatar"}
        width={size}
        height={size}
        style={{ width: size, height: size }}
      />
    );
  }

  return (
    <span
      className="avatar avatar-fallback"
      style={{ width: size, height: size, fontSize: size * 0.4 }}
      aria-hidden
    >
      {initials}
    </span>
  );
}
