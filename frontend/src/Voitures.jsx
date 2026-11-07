import React, { useEffect, useState } from "react";

function Voitures() {
  const [voitures, setVoitures] = useState([]);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState("");
  const [recherche, setRecherche] = useState("");
  const [ville, setVille] = useState("");
  const [marque, setMarque] = useState("");
  const [filtreSite, setFiltreSite] = useState("Tous");
  const [contactProprio, setContactProprio] = useState(null);
  const [dateDebut, setDateDebut] = useState("");
  const [dateFin, setDateFin] = useState("");
  const [messageReservation, setMessageReservation] = useState("");
  const token = localStorage.getItem("token");

  useEffect(() => {
    fetch("http://localhost:8000/api/liste-voitures/")
      .then((res) => res.json())
      .then((data) => {
        setVoitures(data);
        setChargement(false);
      })
      .catch((err) => {
        console.log(err);
        setErreur("Impossible de charger les voitures. Le serveur Django est-il lance ?");
        setChargement(false);
      });
  }, []);

  const sitesDisponibles = ["Tous", ...new Set(voitures.map((v) => v.source).filter(Boolean))];

  const voituresFiltrees = voitures.filter((v) => {
    const search = recherche.toLowerCase();
    const matchesSearch =
      (v.nom && v.nom.toLowerCase().includes(search)) ||
      (v.modele && v.modele.toLowerCase().includes(search)) ||
      (v.marque && v.marque.toLowerCase().includes(search));

    const matchesVille =
      ville === "" ||
      (v.ville && v.ville.toLowerCase().includes(ville.toLowerCase()));

    const matchesMarque =
      marque === "" ||
      (v.marque && v.marque.toLowerCase().includes(marque.toLowerCase()));

    const matchesSite = filtreSite === "Tous" || v.source === filtreSite;

    return matchesSearch && matchesVille && matchesMarque && matchesSite;
  });

  const badgeClass = (source) => {
    if (!source) return "source-badge";
    if (source.includes("Avito")) return "source-badge source-avito";
    if (source.includes("Moteur")) return "source-badge source-moteur";
    if (source.includes("MarocAnnonces")) return "source-badge source-maroc";
    if (source.includes("Proprietaire")) return "source-badge source-proprio";
    return "source-badge source-autre";
  };

  const handleReserver = async (e) => {
    e.preventDefault();
    
    if (!dateDebut || !dateFin) {
      setMessageReservation("Veuillez selectionner les dates");
      return;
    }

    if (!token) {
      setMessageReservation("Veuillez vous connecter pour reserver");
      return;
    }

    try {
      const response = await fetch("http://localhost:8000/api/reservations/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          voiture_id: contactProprio.id,
          date_debut: dateDebut,
          date_fin: dateFin,
        }),
      });

      if (response.ok) {
        setMessageReservation("Demande de reservation envoyee avec succes !");
        setTimeout(() => {
          setContactProprio(null);
          setDateDebut("");
          setDateFin("");
          setMessageReservation("");
        }, 2000);
      } else {
        const data = await response.json();
        setMessageReservation(data.erreur || "Erreur lors de la reservation");
      }
    } catch (error) {
      console.log(error);
      setMessageReservation("Erreur de connexion au serveur");
    }
  };

  return (
    <div className="page-voitures">
      <section className="hero">
        <h1 className="hero-title">Louez la voiture qu'il vous faut</h1>
        <p className="hero-sub">
          Annonces issues de plusieurs sites : Avito.ma, Moteur.ma, MarocAnnonces.com, et nos proprietaires
        </p>
        <div className="search-bar">
          <input
            type="text"
            placeholder="Rechercher un modele (ex: Clio, Logan, Tucson...)"
            value={recherche}
            onChange={(e) => setRecherche(e.target.value)}
          />
          <input
            type="text"
            placeholder="Ville (ex: Casablanca, Rabat...)"
            value={ville}
            onChange={(e) => setVille(e.target.value)}
          />
          <input
            type="text"
            placeholder="Marque (ex: Hyundai, Renault...)"
            value={marque}
            onChange={(e) => setMarque(e.target.value)}
          />
        </div>
      </section>

      {!chargement && !erreur && sitesDisponibles.length > 1 && (
        <div className="filtre-sites">
          <span className="filtre-label">Filtrer par site :</span>
          {sitesDisponibles.map((s) => (
            <button
              key={s}
              className={
                "filtre-btn" + (filtreSite === s ? " filtre-btn-actif" : "")
              }
              onClick={() => setFiltreSite(s)}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {chargement && (
        <div className="loading">
          <div className="spinner"></div>
          <p>Chargement des annonces depuis plusieurs sites...</p>
        </div>
      )}

      {erreur && <div className="error-box">{erreur}</div>}

      {!chargement && !erreur && (
        <>
          <p className="result-count">
            {voituresFiltrees.length} voiture{voituresFiltrees.length > 1 ? "s" : ""} disponible{voituresFiltrees.length > 1 ? "s" : ""} a la location
          </p>

          <div className="grid">
            {voituresFiltrees.map((v, i) => (
              <article key={i} className="card">
                <div className="card-image">
                  {v.image ? (
                    <img src={v.image} alt={v.nom} />
                  ) : (
                    <div
                      className="no-image"
                      style={{
                        width: "100%",
                        height: "200px",
                        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: "white",
                        fontSize: "14px",
                        fontWeight: "bold",
                      }}
                    >
                      🚗 Pas d'image
                    </div>
                  )}
                  <span className={badgeClass(v.source)}>{v.source || "Source inconnue"}</span>
                </div>
                <div className="card-body">
                  <h3 className="card-title">
                    {v.marque || "Marque"} - {v.modele || v.nom}
                  </h3>

                  <div className="card-infos-obligatoires">
                    <p className="card-spec">
                      <strong>Site :</strong> {v.source || "Non specifie"}
                    </p>
                    <p className="card-spec">
                      <strong>Marque :</strong> {v.marque || "Non specifiee"}
                    </p>
                    <p className="card-spec">
                      <strong>Modele :</strong> {v.modele || "Non specifie"}
                    </p>
                  </div>

                  <p className="card-meta">{v.ville}</p>
                  {v.description && (
                    <p className="card-description">{v.description}</p>
                  )}
                  <p className="card-price">{v.prix}</p>
                  {v.is_owner_listing ? (
                    <button
                      onClick={() => setContactProprio(v)}
                      className="card-link"
                    >
                      Reserver / Contacter
                    </button>
                  ) : (
                    <a
                      href={v.url}
                      target="_blank"
                      rel="noreferrer"
                      className="card-link"
                    >
                      Voir sur {v.source}
                    </a>
                  )}
                </div>
              </article>
            ))}
          </div>
        </>
      )}

      {contactProprio && (
        <div className="modal-overlay" onClick={() => setContactProprio(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2 className="modal-title">Reserver cette voiture</h2>
            
            <div className="modal-info">
              <p><strong>Voiture :</strong> {contactProprio.marque} {contactProprio.nom}</p>
              <p><strong>Modele :</strong> {contactProprio.modele}</p>
              <p><strong>Ville :</strong> {contactProprio.ville}</p>
              <p><strong>Prix :</strong> {contactProprio.prix}</p>
            </div>

            {!token ? (
              <div className="modal-info">
                <p style={{ color: "red" }}>Veuillez vous connecter pour reserver une voiture</p>
              </div>
            ) : (
              <form onSubmit={handleReserver} className="reservation-form">
                <div className="form-group">
                  <label>Date de debut :</label>
                  <input
                    type="date"
                    value={dateDebut}
                    onChange={(e) => setDateDebut(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Date de fin :</label>
                  <input
                    type="date"
                    value={dateFin}
                    onChange={(e) => setDateFin(e.target.value)}
                    required
                  />
                </div>
                {messageReservation && (
                  <p style={{ color: messageReservation.includes("succes") ? "green" : "red" }}>
                    {messageReservation}
                  </p>
                )}
                <button type="submit" className="btn-primary">
                  Envoyer la demande
                </button>
              </form>
            )}

            <div className="modal-info modal-contact">
              <p><strong>Proprietaire :</strong> {contactProprio.proprietaire_nom}</p>
              {contactProprio.proprietaire_telephone && (
                <p>
                  <strong>Telephone :</strong>{" "}
                  <a href={"tel:" + contactProprio.proprietaire_telephone}>
                    {contactProprio.proprietaire_telephone}
                  </a>
                </p>
              )}
              {contactProprio.proprietaire_email && (
                <p>
                  <strong>Email :</strong>{" "}
                  <a href={"mailto:" + contactProprio.proprietaire_email}>
                    {contactProprio.proprietaire_email}
                  </a>
                </p>
              )}
            </div>

            <button
              className="btn-secondary"
              onClick={() => setContactProprio(null)}
            >
              Fermer
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default Voitures;
