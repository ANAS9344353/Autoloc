import React, { useState } from "react";

function Login({ setToken, setUsername, setIsOwner, goTo }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage("");
    try {
      const res = await fetch("http://localhost:8000/api/login/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (data.token) {
        localStorage.setItem("token", data.token);
        localStorage.setItem("username", data.username || "");
        localStorage.setItem("isOwner", data.is_owner ? "true" : "false");
        setToken(data.token);
        setUsername(data.username);
        setIsOwner(!!data.is_owner);
        goTo("voitures");
      } else {
        setMessage(data.erreur || "Erreur inconnue");
      }
    } catch (err) {
      setMessage("Impossible de contacter le serveur");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-wrap">
      <div className="auth-card">
        <h2 className="auth-title">Se connecter</h2>
        <p className="auth-sub">Acceder a votre compte AutoLoc</p>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="field">
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="exemple@gmail.com"
              required
            />
          </div>

          <div className="field">
            <label>Mot de passe</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="********"
              required
            />
          </div>

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Connexion..." : "Se connecter"}
          </button>
        </form>

        {message && <p className="auth-error">{message}</p>}

        <p className="auth-link">
          Pas de compte ? <a onClick={() => goTo("signup")}>Créer un compte</a>
        </p>
      </div>
    </div>
  );
}

export default Login;
