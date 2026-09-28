import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../AuthContext";
import Avatar from "../components/Avatar";

function excerpt(html) {
  const text = (html || "").replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
  return text.length > 160 ? `${text.slice(0, 160)}…` : text;
}

export default function Home() {
  const { user } = useAuth();
  const [blogs, setBlogs] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .listBlogs()
      .then(setBlogs)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">A quiet place to write</p>
        <h1>Stories from people who show up.</h1>
        <p className="lede">
          Read the latest posts, or sign in to publish your own.
        </p>
        {user ? (
          <Link to="/new" className="btn btn-primary">
            Write a post
          </Link>
        ) : (
          <Link to="/register" className="btn btn-primary">
            Start writing
          </Link>
        )}
      </section>

      <section className="feed">
        <h2>Latest posts</h2>
        {loading && <p className="muted">Loading…</p>}
        {error && <p className="error">{error}</p>}
        {!loading && !error && blogs.length === 0 && (
          <p className="muted">No posts yet. Be the first to write one.</p>
        )}
        <ul className="post-list">
          {blogs.map((blog) => (
            <li key={blog.id}>
              <article className="post-link">
                <Link to={`/posts/${blog.id}`}>
                  <h3>{blog.title}</h3>
                  <p className="post-excerpt">{excerpt(blog.content)}</p>
                </Link>
                <div className="post-meta-row">
                  <Link
                    to={`/users/${blog.author_username}`}
                    className="author-link"
                  >
                    <Avatar
                      src={blog.author_avatar_url}
                      name={blog.author_username}
                      size={28}
                    />
                    <span>{blog.author_username}</span>
                  </Link>
                  <span className="post-meta">
                    {new Date(blog.created_at).toLocaleDateString()} ·{" "}
                    {blog.like_count || 0} likes · {blog.comment_count || 0} comments
                  </span>
                </div>
              </article>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
