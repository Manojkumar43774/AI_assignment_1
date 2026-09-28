import { useEffect, useState } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../AuthContext";
import RichTextEditor, { isEditorEmpty } from "../components/RichTextEditor";

export default function EditBlog() {
  const { id } = useParams();
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!user) return;
    api
      .getBlog(id)
      .then((blog) => {
        if (blog.author_id !== user.id) {
          setError("You can only edit your own posts.");
          return;
        }
        setTitle(blog.title);
        setContent(blog.content);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id, user]);

  if (authLoading) {
    return (
      <main className="page">
        <p className="muted">Loading…</p>
      </main>
    );
  }
  if (!user) return <Navigate to="/login" replace />;

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (isEditorEmpty(content)) {
      setError("Write some content before saving.");
      return;
    }
    setSubmitting(true);
    try {
      const blog = await api.updateBlog(id, { title, content });
      navigate(`/posts/${blog.id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <main className="page">
        <p className="muted">Loading…</p>
      </main>
    );
  }

  return (
    <main className="page editor-page">
      <Link to={`/posts/${id}`} className="back">
        ← Back to post
      </Link>
      <h1>Edit post</h1>
      <form className="form" onSubmit={handleSubmit}>
        {error && <p className="error">{error}</p>}
        <label>
          Title
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            maxLength={200}
            required
          />
        </label>
        <div>
          <span className="field-label">Content</span>
          <RichTextEditor value={content} onChange={setContent} />
        </div>
        <button className="btn btn-primary" type="submit" disabled={submitting}>
          {submitting ? "Saving…" : "Save changes"}
        </button>
      </form>
    </main>
  );
}
