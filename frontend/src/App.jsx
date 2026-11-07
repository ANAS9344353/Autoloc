import React, { useState } from "react";
import Login from "./Login";
import Signup from "./Signup";
import Voitures from "./Voitures";
import MesVoitures from "./MesVoitures";
import MesReservations from "./MesReservations";
import "./App.css";

function App() {
  const [page, setPage] = useState("login");
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [username, setUsername] = useState(localStorage.getItem("username") || "");
  const [isOwner, setIsOwner] = useState(localStorage.getItem("isOwner") === "true");

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    localStorage.removeItem("isOwner");
    setToken("");
    setUsername("");
    setIsOwner(false);
    setPage("login");
  };

  return (
    <div className="app">
      {page !== "login" && page !== "signup" && (
        <header className="header">
          <div className="header-inner">
            <div className="logo" onClick={() => setPage("voitures")}>
              AutoLoc
            </div>
            <nav className="nav">
              <a
                className={page === "voitures" ? "nav-link active" : "nav-link"}
                onClick={() => setPage("voitures")}
              >
                Voitures
              </a>
              {token && isOwner && (
                <a
                  className={
                    page === "mes-voitures" ? "nav-link active" : "nav-link"
                  }
                  onClick={() => setPage("mes-voitures")}
                >
                  Mes voitures
                </a>
              )}
              {token && (
                <a
                  className={
                    page === "mes-reservations" ? "nav-link active" : "nav-link"
                  }
                  onClick={() => setPage("mes-reservations")}
                >
                  Mes reservations
                </a>
              )}
              {!token ? (
                <>
                  <a
                    className={page === "login" ? "nav-link active" : "nav-link"}
                    onClick={() => setPage("login")}
                  >
                    Connexion
                  </a>
                  <a
                    className={page === "signup" ? "nav-link active" : "nav-link"}
                    onClick={() => setPage("signup")}
                  >
                    Inscription
                  </a>
                </>
              ) : (
                <>
                  <span className="nav-user">Bonjour, {username}</span>
                  <a className="nav-link" onClick={handleLogout}>Deconnexion</a>
                </>
              )}
            </nav>
          </div>
        </header>
      )}

      <main className="main">
        {page === "login" && (
          <Login
            setToken={setToken}
            setUsername={setUsername}
            setIsOwner={setIsOwner}
            goTo={setPage}
          />
        )}
        {page === "signup" && (
          <Signup
            setToken={setToken}
            setUsername={setUsername}
            setIsOwner={setIsOwner}
            goTo={setPage}
          />
        )}
        {page === "voitures" && <Voitures />}
        {page === "mes-voitures" && isOwner && <MesVoitures token={token} />}
        {page === "mes-reservations" && token && <MesReservations />}
      </main>

      {page !== "login" && page !== "signup" && (
        <footer className="footer">
          <p>AutoLoc - Location de voitures au Maroc</p>
          <p className="footer-small">
            Annonces issues d'Avito.ma, Moteur.ma, MarocAnnonces.com et proprietaires AutoLoc
          </p>
        </footer>
      )}
    </div>
  );
}

export default App;
