const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function authHeaders() {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request(path, options = {}) {
  const headers = {
    ...authHeaders(),
    ...options.headers,
  };
  if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 204) return null;

  const text = await res.text();
  const data = text ? JSON.parse(text) : null;

  if (!res.ok) {
    const detail = data?.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d) => d.msg).join(", ")
          : "Request failed";
    throw new Error(message);
  }

  return data;
}

export const api = {
  apiUrl: API_URL,

  providers: () => request("/api/auth/providers"),

  googleLoginUrl: () => `${API_URL}/api/auth/google`,

  me: () => request("/api/auth/me"),

  listBlogs: () => request("/api/blogs"),

  listMyBlogs: () => request("/api/blogs/mine"),

  getBlog: (id) => request(`/api/blogs/${id}`),

  createBlog: (body) =>
    request("/api/blogs", { method: "POST", body: JSON.stringify(body) }),

  updateBlog: (id, body) =>
    request(`/api/blogs/${id}`, { method: "PUT", body: JSON.stringify(body) }),

  deleteBlog: (id) => request(`/api/blogs/${id}`, { method: "DELETE" }),

  toggleLike: (id) => request(`/api/blogs/${id}/like`, { method: "POST" }),

  listComments: (id) => request(`/api/blogs/${id}/comments`),

  createComment: (id, body) =>
    request(`/api/blogs/${id}/comments`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  deleteComment: (blogId, commentId) =>
    request(`/api/blogs/${blogId}/comments/${commentId}`, { method: "DELETE" }),

  getProfile: (username) => request(`/api/users/${username}`),

  getUserBlogs: (username) => request(`/api/users/${username}/blogs`),

  updateProfile: (body) =>
    request("/api/users/me", { method: "PATCH", body: JSON.stringify(body) }),

  uploadAvatar: (file) => {
    const form = new FormData();
    form.append("file", file);
    return request("/api/users/me/avatar", { method: "POST", body: form });
  },
};
