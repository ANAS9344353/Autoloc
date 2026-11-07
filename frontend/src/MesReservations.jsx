import React, { useEffect, useState } from "react";

function MesReservations() {
  const [reservations, setReservations] = useState([]);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState("");
  const [activeTab, setActiveTab] = useState("proprietaire"); // proprietaire ou client
  const token = localStorage.getItem("token");

  useEffect(() => {
    if (!token) {
      setErreur("Veuillez vous connecter");
      setChargement(false);
      return;
    }

    chargerReservations();
  }, [token, activeTab]);

  const chargerReservations = async () => {
    try {
      const endpoint =
        activeTab === "proprietaire"
          ? "http://localhost:8000/api/mes-reservations-proprietaire/"
          : "http://localhost:8000/api/mes-reservations-client/";

      const response = await fetch(endpoint, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setReservations(data);
        setChargement(false);
      } else {
        setErreur("Impossible de charger les reservations");
        setChargement(false);
      }
    } catch (error) {
      console.log(error);
      setErreur("Erreur de connexion au serveur");
      setChargement(false);
    }
  };

  const handleAccepter = async (reservationId) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/reservations/${reservationId}/accepter/`,
        {
          method: "PATCH",
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (response.ok) {
        chargerReservations();
      } else {
        alert("Erreur lors de l'acceptation");
      }
    } catch (error) {
      console.log(error);
      alert("Erreur de connexion");
    }
  };

  const handleRejeter = async (reservationId) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/reservations/${reservationId}/rejeter/`,
        {
          method: "PATCH",
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (response.ok) {
        chargerReservations();
      } else {
        alert("Erreur lors du rejet");
      }
    } catch (error) {
      console.log(error);
      alert("Erreur de connexion");
    }
  };

  const getStatutColor = (statut) => {
    switch (statut) {
      case "PENDING":
        return "orange";
      case "ACCEPTEE":
        return "green";
      case "REJETEE":
        return "red";
      default:
        return "gray";
    }
  };

  const formatDate = (date) => new Date(date).toLocaleDateString("fr-FR");

  const escapeHtml = (value) =>
    String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");

  const formatMontant = (value) => {
    if (value === null || value === undefined || value === "") {
      return "A confirmer";
    }
    return `${Number(value).toFixed(2)} DH`;
  };

  const telechargerFacture = (reservation) => {
    const numero = `FAC-${String(reservation.id).padStart(5, "0")}`;
    const total = formatMontant(reservation.total);
    const prixJour =
      reservation.prix_jour === null || reservation.prix_jour === undefined
        ? reservation.prix
        : formatMontant(reservation.prix_jour);

    const factureHtml = `<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <title>Facture ${escapeHtml(numero)}</title>
  <style>
    body { font-family: Arial, sans-serif; color: #222; margin: 40px; }
    .top { display: flex; justify-content: space-between; gap: 24px; border-bottom: 3px solid #c8102e; padding-bottom: 18px; }
    h1 { margin: 0; color: #c8102e; font-size: 30px; }
    h2 { margin-top: 28px; font-size: 18px; color: #333; }
    .muted { color: #666; font-size: 13px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 24px; }
    .box { border: 1px solid #ddd; border-radius: 8px; padding: 16px; }
    table { width: 100%; border-collapse: collapse; margin-top: 14px; }
    th, td { border-bottom: 1px solid #e5e5e5; padding: 12px; text-align: left; }
    th { background: #f7f7f7; }
    .total { text-align: right; font-size: 22px; font-weight: 700; color: #0a7a36; margin-top: 18px; }
    .footer { margin-top: 36px; font-size: 12px; color: #777; }
    @media print { body { margin: 24px; } }
  </style>
</head>
<body>
  <div class="top">
    <div>
      <h1>AutoLoc</h1>
      <p class="muted">Facture de reservation acceptee</p>
    </div>
    <div>
      <p><strong>Facture :</strong> ${escapeHtml(numero)}</p>
      <p><strong>Date :</strong> ${escapeHtml(new Date().toLocaleDateString("fr-FR"))}</p>
      <p><strong>Reservation :</strong> #${escapeHtml(reservation.id)}</p>
    </div>
  </div>

  <div class="grid">
    <div class="box">
      <h2>Client</h2>
      <p><strong>Nom :</strong> ${escapeHtml(reservation.client_info.nom)}</p>
      <p><strong>Email :</strong> ${escapeHtml(reservation.client_info.email)}</p>
      <p><strong>Telephone :</strong> ${escapeHtml(reservation.client_info.telephone || "Non renseigne")}</p>
    </div>
    <div class="box">
      <h2>Proprietaire</h2>
      <p><strong>Nom :</strong> ${escapeHtml(reservation.proprietaire_info.nom)}</p>
      <p><strong>Email :</strong> ${escapeHtml(reservation.proprietaire_info.email)}</p>
      <p><strong>Telephone :</strong> ${escapeHtml(reservation.proprietaire_info.telephone || "Non renseigne")}</p>
    </div>
  </div>

  <h2>Details de location</h2>
  <table>
    <thead>
      <tr>
        <th>Voiture</th>
        <th>Ville</th>
        <th>Periode</th>
        <th>Jours</th>
        <th>Prix / jour</th>
        <th>Total</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>${escapeHtml(reservation.voiture_nom)}</td>
        <td>${escapeHtml(reservation.ville)}</td>
        <td>Du ${escapeHtml(formatDate(reservation.date_debut))} au ${escapeHtml(formatDate(reservation.date_fin))}</td>
        <td>${escapeHtml(reservation.nb_jours)}</td>
        <td>${escapeHtml(prixJour)}</td>
        <td>${escapeHtml(total)}</td>
      </tr>
    </tbody>
  </table>
  <p class="total">Total: ${escapeHtml(total)}</p>
  <p class="footer">Cette facture est generee automatiquement apres acceptation de la reservation par le proprietaire.</p>
</body>
</html>`;

    const blob = new Blob([factureHtml], { type: "text/html;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${numero}.html`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="mes-reservations-page">
      <h1>Gestion des reservations</h1>

      {/* Tabs */}
      <div className="reservation-tabs">
        <button
          className={`tab-btn ${activeTab === "proprietaire" ? "active" : ""}`}
          onClick={() => {
            setActiveTab("proprietaire");
            setChargement(true);
          }}
        >
          Demandes recues (Proprietaire)
        </button>
        <button
          className={`tab-btn ${activeTab === "client" ? "active" : ""}`}
          onClick={() => {
            setActiveTab("client");
            setChargement(true);
          }}
        >
          Mes reservations (Client)
        </button>
      </div>

      {chargement && (
        <div className="loading">
          <div className="spinner"></div>
          <p>Chargement...</p>
        </div>
      )}

      {erreur && <div className="error-box">{erreur}</div>}

      {!chargement && !erreur && (
        <div className="reservations-list">
          {reservations.length === 0 ? (
            <p className="no-data">
              {activeTab === "proprietaire"
                ? "Aucune demande de reservation"
                : "Aucune reservation"}
            </p>
          ) : (
            reservations.map((r) => (
              <div key={r.id} className="reservation-card">
                <div className="reservation-header">
                  <h3>{r.voiture_nom}</h3>
                  <span
                    className="statut-badge"
                    style={{ backgroundColor: getStatutColor(r.statut) }}
                  >
                    {r.statut === "PENDING"
                      ? "En attente"
                      : r.statut === "ACCEPTEE"
                      ? "Acceptee"
                      : "Rejetee"}
                  </span>
                </div>

                <div className="reservation-details">
                  <p>
                    <strong>{activeTab === "client" ? "Proprietaire" : "Client"} :</strong>{" "}
                    {activeTab === "client" ? r.proprietaire_info.nom : r.client_info.nom}
                  </p>
                  <p>
                    <strong>Email :</strong>{" "}
                    <a
                      href={`mailto:${
                        activeTab === "client"
                          ? r.proprietaire_info.email
                          : r.client_info.email
                      }`}
                    >
                      {activeTab === "client"
                        ? r.proprietaire_info.email
                        : r.client_info.email}
                    </a>
                  </p>
                  {(activeTab === "client"
                    ? r.proprietaire_info.telephone
                    : r.client_info.telephone) && (
                    <p>
                      <strong>Telephone :</strong>{" "}
                      <a
                        href={`tel:${
                          activeTab === "client"
                            ? r.proprietaire_info.telephone
                            : r.client_info.telephone
                        }`}
                      >
                        {activeTab === "client"
                          ? r.proprietaire_info.telephone
                          : r.client_info.telephone}
                      </a>
                    </p>
                  )}
                  <p>
                    <strong>Du :</strong> {formatDate(r.date_debut)}
                  </p>
                  <p>
                    <strong>Au :</strong> {formatDate(r.date_fin)}
                  </p>
                  <p>
                    <strong>Prix :</strong> {r.prix}
                  </p>
                  <p>
                    <strong>Total estime :</strong> {formatMontant(r.total)}
                  </p>
                </div>

                {activeTab === "proprietaire" && r.statut === "PENDING" && (
                  <div className="reservation-actions">
                    <button
                      className="btn-accepter"
                      onClick={() => handleAccepter(r.id)}
                    >
                      ✓ Accepter
                    </button>
                    <button
                      className="btn-rejeter"
                      onClick={() => handleRejeter(r.id)}
                    >
                      ✗ Rejeter
                    </button>
                  </div>
                )}

                {activeTab === "client" && r.statut === "ACCEPTEE" && (
                  <div className="reservation-actions">
                    <button
                      className="btn-facture"
                      onClick={() => telechargerFacture(r)}
                    >
                      Telecharger la facture
                    </button>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

export default MesReservations;
