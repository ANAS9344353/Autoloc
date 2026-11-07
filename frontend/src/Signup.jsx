import React, { useState } from "react";

function Signup({ setToken, setUsername, setIsOwner, goTo }) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [accountType, setAccountType] = useState("client"); // "client" ou "proprietaire"
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handlePhoneChange = (e) => {
    const value = e.target.value.replace(/\D/g, "");
    setPhone(value.slice(0, 10));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage("");

    if (phone.length !== 10) {
      setMessage("Le numéro de téléphone doit contenir exactement 10 chiffres");
      setLoading(false);
      return;
    }

    try {
      const res = await fetch("http://localhost:8000/api/signup/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          password,
          full_name: fullName,
          phone_number: phone,
          is_owner: accountType === "proprietaire",
        }),
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
        <h2 className="auth-title">Creer un compte</h2>
        <p className="auth-sub">Rejoignez AutoLoc en quelques secondes</p>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="field">
            <label>Type de compte</label>
            <div className="account-type">
              <label
                className={
                  "account-type-option" +
                  (accountType === "client" ? " selected" : "")
                }
              >
                <input
                  type="radio"
                  name="accountType"
                  value="client"
                  checked={accountType === "client"}
                  onChange={() => setAccountType("client")}
                />
                <span>Client (louer une voiture)</span>
              </label>
              <label
                className={
                  "account-type-option" +
                  (accountType === "proprietaire" ? " selected" : "")
                }
              >
                <input
                  type="radio"
                  name="accountType"
                  value="proprietaire"
                  checked={accountType === "proprietaire"}
                  onChange={() => setAccountType("proprietaire")}
                />
                <span>Proprietaire (mettre ma voiture en location)</span>
              </label>
            </div>
          </div>

          <div className="field">
            <label>Nom complet</label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Entrez votre nom"
              required
            />
          </div>

          <div className="field">
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="jean@example.com"
              required
            />
          </div>

          <div className="field">
            <label>Mot de passe</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Au moins 6 caracteres"
              required
            />
          </div>

          <div className="field">
            <label>Numero de telephone (10 chiffres)</label>
            <input
              type="tel"
              value={phone}
              onChange={handlePhoneChange}
              placeholder="Ex: 0612345678"
              maxLength="10"
              required
            />
            {phone && phone.length !== 10 && (
              <p style={{ color: "#a02020", fontSize: "12px", marginTop: "4px" }}>
                {phone.length} / 10 chiffres
              </p>
            )}
          </div>

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Creation..." : "Creer mon compte"}
          </button>
        </form>

        {message && <p className="auth-error">{message}</p>}

        <p className="auth-link">
          Vous avez deja un compte ? <a onClick={() => goTo("login")}>Se connecter</a>
        </p>
      </div>
    </div>
  );
}

export default Signup;
