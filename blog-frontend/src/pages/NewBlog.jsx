import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../AuthContext";
import RichTextEditor, { isEditorEmpty } from "../components/RichTextEditor";

export default function NewBlog() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (loading) {
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
      setError("Write some content before publishing.");
      return;
    }
    setSubmitting(true);
    try {
      const blog = await api.createBlog({ title, content });
      navigate(`/posts/${blog.id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="page editor-page">
      <h1>New post</h1>
      <p className="lede">Write something worth reading.</p>
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
          {submitting ? "Publishing…" : "Publish"}
        </button>
      </form>
    </main>
  );
}
