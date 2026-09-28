import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../AuthContext";
import Avatar from "../components/Avatar";

export default function Profile() {
  const { user, loading: authLoading, refreshUser } = useAuth();
  const [bio, setBio] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    if (user) setBio(user.bio || "");
  }, [user]);

  if (authLoading) {
    return (
      <main className="page">
        <p className="muted">Loading…</p>
      </main>
    );
  }
  if (!user) return <Navigate to="/login" replace />;

  async function handleSave(e) {
    e.preventDefault();
    setError("");
    setMessage("");
    setSaving(true);
    try {
      const updated = await api.updateProfile({ bio });
      refreshUser(updated);
      setMessage("Profile saved.");
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleAvatar(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setError("");
    setMessage("");
    setUploading(true);
    try {
      const updated = await api.uploadAvatar(file);
      refreshUser(updated);
      setMessage("Photo updated.");
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  return (
    <main className="page narrow">
      <h1>Your profile</h1>
      <p className="lede">
        Add a photo and bio. Others can view your public page and blogs.
      </p>

      <div className="profile-card">
        <Avatar src={user.avatar_url} name={user.username} size={88} />
        <div>
          <h2 className="profile-name">{user.username}</h2>
          <p className="muted">{user.email}</p>
          <Link to={`/users/${user.username}`}>View public profile →</Link>
        </div>
      </div>

      <form className="form" onSubmit={handleSave}>
        {error && <p className="error">{error}</p>}
        {message && <p className="success">{message}</p>}

        <label className="file-label">
          Profile photo
          <input type="file" accept="image/jpeg,image/png,image/webp" onChange={handleAvatar} />
          <span className="btn btn-ghost">
            {uploading ? "Uploading…" : "Choose photo"}
          </span>
        </label>

        <label>
          Bio
          <textarea
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            rows={4}
            maxLength={500}
            placeholder="A short intro about you"
          />
        </label>
        <button className="btn btn-primary" type="submit" disabled={saving}>
          {saving ? "Saving…" : "Save profile"}
        </button>
      </form>
    </main>
  );
}
