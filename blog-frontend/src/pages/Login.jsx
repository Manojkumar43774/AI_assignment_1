import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

export default function Login({ mode = "login" }) {
  const [providers, setProviders] = useState({ google: false });
  const [error, setError] = useState("");
  const isSignup = mode === "signup";

  useEffect(() => {
    api
      .providers()
      .then(setProviders)
      .catch((err) => setError(err.message));
  }, []);

  return (
    <main className="page narrow">
      <h1>{isSignup ? "Create an account" : "Welcome back"}</h1>
      <p className="lede">
        {isSignup
          ? "Sign up with Google to start publishing."
          : "Log in with Google to continue."}
      </p>

      {error && <p className="error">{error}</p>}

      {!error && !providers.google && (
        <p className="error">
          Google OAuth is not configured yet. Add{" "}
          <code>GOOGLE_CLIENT_ID</code> and <code>GOOGLE_CLIENT_SECRET</code> to{" "}
          <code>backend/.env</code>, then restart the API.
        </p>
      )}

      <div className="oauth-stack">
        {providers.google && (
          <a className="btn btn-oauth" href={api.googleLoginUrl()}>
            Continue with Google
          </a>
        )}
      </div>

      <p className="muted">
        {isSignup ? (
          <>
            Already have an account? <Link to="/login">Log in</Link>
          </>
        ) : (
          <>
            New here? <Link to="/register">Sign up</Link>
          </>
        )}
      </p>
    </main>
  );
}
