import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../AuthContext";
import Avatar, { sanitizeHtml } from "../components/Avatar";

export default function PostDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [blog, setBlog] = useState(null);
  const [comments, setComments] = useState([]);
  const [commentText, setCommentText] = useState("");
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");
  const [loading, setLoading] = useState(true);
  const [liking, setLiking] = useState(false);
  const [commenting, setCommenting] = useState(false);

  useEffect(() => {
    Promise.all([api.getBlog(id), api.listComments(id)])
      .then(([post, commentList]) => {
        setBlog(post);
        setComments(commentList);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  const isOwner = user && blog && user.id === blog.author_id;

  async function handleLike() {
    if (!user) {
      navigate("/login");
      return;
    }
    setLiking(true);
    setActionError("");
    try {
      const result = await api.toggleLike(id);
      setBlog((prev) => ({
        ...prev,
        liked_by_me: result.liked,
        like_count: result.like_count,
      }));
    } catch (err) {
      setActionError(err.message);
    } finally {
      setLiking(false);
    }
  }

  async function handleDelete() {
    if (!window.confirm("Delete this post permanently?")) return;
    setActionError("");
    try {
      await api.deleteBlog(id);
      navigate("/my-blogs");
    } catch (err) {
      setActionError(err.message);
    }
  }

  async function handleComment(e) {
    e.preventDefault();
    if (!user) {
      navigate("/login");
      return;
    }
    setCommenting(true);
    setActionError("");
    try {
      const created = await api.createComment(id, { content: commentText });
      setComments((prev) => [...prev, created]);
      setCommentText("");
      setBlog((prev) => ({
        ...prev,
        comment_count: (prev.comment_count || 0) + 1,
      }));
    } catch (err) {
      setActionError(err.message);
    } finally {
      setCommenting(false);
    }
  }

  async function handleDeleteComment(commentId) {
    setActionError("");
    try {
      await api.deleteComment(id, commentId);
      setComments((prev) => prev.filter((c) => c.id !== commentId));
      setBlog((prev) => ({
        ...prev,
        comment_count: Math.max((prev.comment_count || 1) - 1, 0),
      }));
    } catch (err) {
      setActionError(err.message);
    }
  }

  if (loading) {
    return (
      <main className="page">
        <p className="muted">Loading…</p>
      </main>
    );
  }

  if (error || !blog) {
    return (
      <main className="page">
        <p className="error">{error || "Post not found"}</p>
        <Link to="/">Back to posts</Link>
      </main>
    );
  }

  return (
    <main className="page article">
      <Link to="/" className="back">
        ← All posts
      </Link>
      <h1>{blog.title}</h1>
      <div className="author-row">
        <Link to={`/users/${blog.author_username}`} className="author-link">
          <Avatar
            src={blog.author_avatar_url}
            name={blog.author_username}
            size={36}
          />
          <span>{blog.author_username}</span>
        </Link>
        <span className="post-meta">
          {new Date(blog.created_at).toLocaleString()}
          {blog.updated_at && blog.updated_at !== blog.created_at
            ? ` · edited ${new Date(blog.updated_at).toLocaleString()}`
            : ""}
        </span>
      </div>

      <div className="post-actions">
        <button
          type="button"
          className={`btn btn-ghost ${blog.liked_by_me ? "liked" : ""}`}
          onClick={handleLike}
          disabled={liking}
        >
          {blog.liked_by_me ? "Liked" : "Like"} · {blog.like_count || 0}
        </button>
        {isOwner && (
          <>
            <Link to={`/posts/${blog.id}/edit`} className="btn btn-ghost">
              Edit
            </Link>
            <button type="button" className="btn btn-danger" onClick={handleDelete}>
              Delete
            </button>
          </>
        )}
      </div>

      {actionError && <p className="error">{actionError}</p>}

      <div
        className="article-body prose"
        dangerouslySetInnerHTML={{ __html: sanitizeHtml(blog.content) }}
      />

      <section className="comments">
        <h2>Comments ({comments.length})</h2>

        {user ? (
          <form className="form comment-form" onSubmit={handleComment}>
            <label>
              Add a comment
              <textarea
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                rows={3}
                required
                maxLength={2000}
              />
            </label>
            <button className="btn btn-primary" type="submit" disabled={commenting}>
              {commenting ? "Posting…" : "Post comment"}
            </button>
          </form>
        ) : (
          <p className="muted">
            <Link to="/login">Log in</Link> to like or comment.
          </p>
        )}

        <ul className="comment-list">
          {comments.map((comment) => {
            const canDelete =
              user && (user.id === comment.user_id || user.id === blog.author_id);
            return (
              <li key={comment.id} className="comment-item">
                <div className="comment-header">
                  <Link
                    to={`/users/${comment.username}`}
                    className="author-link"
                  >
                    <Avatar
                      src={comment.avatar_url}
                      name={comment.username}
                      size={28}
                    />
                    <strong>{comment.username}</strong>
                  </Link>
                  <span className="muted">
                    {new Date(comment.created_at).toLocaleString()}
                  </span>
                </div>
                <p>{comment.content}</p>
                {canDelete && (
                  <button
                    type="button"
                    className="btn btn-ghost btn-small"
                    onClick={() => handleDeleteComment(comment.id)}
                  >
                    Delete
                  </button>
                )}
              </li>
            );
          })}
        </ul>
        {comments.length === 0 && <p className="muted">No comments yet.</p>}
      </section>
    </main>
  );
}
