import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../AuthContext";

export default function MyBlogs() {
  const { user, loading: authLoading } = useAuth();
  const [blogs, setBlogs] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    api
      .listMyBlogs()
      .then(setBlogs)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [user]);

  if (authLoading) {
    return (
      <main className="page">
        <p className="muted">Loading…</p>
      </main>
    );
  }
  if (!user) return <Navigate to="/login" replace />;

  async function handleDelete(id) {
    if (!window.confirm("Delete this post permanently?")) return;
    try {
      await api.deleteBlog(id);
      setBlogs((prev) => prev.filter((b) => b.id !== id));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <main className="page">
      <div className="section-head">
        <div>
          <h1>My blogs</h1>
          <p className="lede">Create, edit, and delete your posts.</p>
        </div>
        <Link to="/new" className="btn btn-primary">
          Write a post
        </Link>
      </div>

      {loading && <p className="muted">Loading…</p>}
      {error && <p className="error">{error}</p>}
      {!loading && blogs.length === 0 && (
        <p className="muted">You haven’t published anything yet.</p>
      )}

      <ul className="post-list">
        {blogs.map((blog) => (
          <li key={blog.id} className="manage-item">
            <Link to={`/posts/${blog.id}`} className="post-link">
              <h3>{blog.title}</h3>
              <p className="post-meta">
                {new Date(blog.created_at).toLocaleDateString()} ·{" "}
                {blog.like_count || 0} likes · {blog.comment_count || 0} comments
              </p>
            </Link>
            <div className="manage-actions">
              <Link to={`/posts/${blog.id}/edit`} className="btn btn-ghost">
                Edit
              </Link>
              <button
                type="button"
                className="btn btn-danger"
                onClick={() => handleDelete(blog.id)}
              >
                Delete
              </button>
            </div>
          </li>
        ))}
      </ul>
    </main>
  );
}
