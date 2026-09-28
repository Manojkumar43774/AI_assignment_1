import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import Avatar from "../components/Avatar";

function excerpt(html) {
  const text = html.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
  return text.length > 160 ? `${text.slice(0, 160)}…` : text;
}

export default function UserProfile() {
  const { username } = useParams();
  const [profile, setProfile] = useState(null);
  const [blogs, setBlogs] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([api.getProfile(username), api.getUserBlogs(username)])
      .then(([user, posts]) => {
        setProfile(user);
        setBlogs(posts);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [username]);

  if (loading) {
    return (
      <main className="page">
        <p className="muted">Loading…</p>
      </main>
    );
  }

  if (error || !profile) {
    return (
      <main className="page">
        <p className="error">{error || "User not found"}</p>
        <Link to="/">Back to posts</Link>
      </main>
    );
  }

  return (
    <main className="page">
      <section className="profile-hero">
        <Avatar src={profile.avatar_url} name={profile.username} size={96} />
        <div>
          <h1>{profile.username}</h1>
          {profile.bio ? (
            <p className="lede">{profile.bio}</p>
          ) : (
            <p className="muted">No bio yet.</p>
          )}
          <p className="post-meta">
            {profile.blog_count} {profile.blog_count === 1 ? "post" : "posts"} · joined{" "}
            {new Date(profile.created_at).toLocaleDateString()}
          </p>
        </div>
      </section>

      <section className="feed">
        <h2>Posts by {profile.username}</h2>
        {blogs.length === 0 && <p className="muted">No posts yet.</p>}
        <ul className="post-list">
          {blogs.map((blog) => (
            <li key={blog.id}>
              <Link to={`/posts/${blog.id}`} className="post-link">
                <h3>{blog.title}</h3>
                <p className="post-excerpt">{excerpt(blog.content)}</p>
                <p className="post-meta">
                  {new Date(blog.created_at).toLocaleDateString()} ·{" "}
                  {blog.like_count || 0} likes · {blog.comment_count || 0} comments
                </p>
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
