import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../AuthContext";

export default function AuthCallback() {
  const { completeOAuth } = useAuth();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState("");

  useEffect(() => {
    const token = params.get("token");
    if (!token) {
      setError("Missing auth token from provider.");
      return;
    }
    completeOAuth(token)
      .then(() => navigate("/", { replace: true }))
      .catch((err) => setError(err.message));
  }, [params, completeOAuth, navigate]);

  return (
    <main className="page narrow">
      <h1>Signing you in…</h1>
      {error ? <p className="error">{error}</p> : <p className="muted">Finishing OAuth…</p>}
    </main>
  );
}
