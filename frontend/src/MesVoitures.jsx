import React, { useEffect, useState } from "react";

function MesVoitures({ token }) {
  const [mesVoitures, setMesVoitures] = useState([]);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState("");
  const [message, setMessage] = useState("");

  // Formulaire
  const [nom, setNom] = useState("");
  const [marque, setMarque] = useState("");
  const [ville, setVille] = useState("");
  const [description, setDescription] = useState("");
  const [prix, setPrix] = useState("");
  const [photo, setPhoto] = useState(null);
  const [envoi, setEnvoi] = useState(false);

  // Edition
  const [editingId, setEditingId] = useState(null);
  const [editingData, setEditingData] = useState({});

  const chargerVoitures = () => {
    setChargement(true);
    fetch("http://localhost:8000/api/mes-voitures/", {
      headers: { Authorization: "Bearer " + token },
    })
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setMesVoitures(data);
        } else {
          setErreur(data.erreur || "Erreur lors du chargement");
        }
        setChargement(false);
      })
      .catch(() => {
        setErreur("Impossible de contacter le serveur");
        setChargement(false);
      });
  };

  useEffect(() => {
    chargerVoitures();
    // eslint-disable-next-line
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage("");
    setErreur("");

    // Si en mode édition
    if (editingId) {
      if (!editingData.nom || !editingData.marque || !editingData.ville) {
        setErreur("Veuillez remplir au moins le nom, la marque et la ville");
        return;
      }

      const formData = new FormData();
      formData.append("nom", editingData.nom);
      formData.append("marque", editingData.marque);
      formData.append("ville", editingData.ville);
      formData.append("description", editingData.description || "");
      formData.append("prix", editingData.prix || "");
      if (editingData.photo && typeof editingData.photo !== "string") {
        formData.append("photo", editingData.photo);
      }

      setEnvoi(true);
      try {
        const res = await fetch("http://localhost:8000/api/mes-voitures/" + editingId + "/", {
          method: "PUT",
          headers: { Authorization: "Bearer " + token },
          body: formData,
        });
        const data = await res.json();
        if (res.ok) {
          setMessage("Voiture modifiee avec succes !");
          setEditingId(null);
          setEditingData({});
          chargerVoitures();
        } else {
          setErreur(data.erreur || "Erreur lors de la modification");
        }
      } catch (err) {
        setErreur("Impossible de contacter le serveur");
      } finally {
        setEnvoi(false);
      }
      return;
    }

    // Mode ajout
    if (!nom || !marque || !ville) {
      setErreur("Veuillez remplir au moins le nom, la marque et la ville");
      return;
    }

    const formData = new FormData();
    formData.append("nom", nom);
    formData.append("marque", marque);
    formData.append("ville", ville);
    formData.append("description", description);
    formData.append("prix", prix);
    if (photo) {
      formData.append("photo", photo);
    }

    setEnvoi(true);
    try {
      const res = await fetch("http://localhost:8000/api/mes-voitures/", {
        method: "POST",
        headers: { Authorization: "Bearer " + token },
        body: formData,
      });
      const data = await res.json();
      if (res.ok) {
        setMessage("Voiture ajoutee avec succes !");
        setNom("");
        setMarque("");
        setVille("");
        setDescription("");
        setPrix("");
        setPhoto(null);
        // Reset l'input file
        const fileInput = document.getElementById("photo-input");
        if (fileInput) fileInput.value = "";
        chargerVoitures();
      } else {
        setErreur(data.erreur || "Erreur lors de l'ajout");
      }
    } catch (err) {
      setErreur("Impossible de contacter le serveur");
    } finally {
      setEnvoi(false);
    }
  };

  const supprimer = async (id) => {
    if (!window.confirm("Etes-vous sur de vouloir supprimer cette voiture ?")) {
      return;
    }
    try {
      const res = await fetch("http://localhost:8000/api/mes-voitures/" + id + "/", {
        method: "DELETE",
        headers: { Authorization: "Bearer " + token },
      });
      if (res.ok) {
        chargerVoitures();
      } else {
        const data = await res.json();
        setErreur(data.erreur || "Erreur lors de la suppression");
      }
    } catch (err) {
      setErreur("Impossible de contacter le serveur");
    }
  };

  const commencerEdition = (voiture) => {
    setEditingId(voiture.id);
    setEditingData({
      nom: voiture.nom,
      marque: voiture.marque,
      ville: voiture.ville,
      description: voiture.description || "",
      prix: voiture.prix || "",
      photo: voiture.image || null,
    });
    setMessage("");
    setErreur("");
  };

  const annulerEdition = () => {
    setEditingId(null);
    setEditingData({});
    setMessage("");
    setErreur("");
  };

  return (
    <div className="page-voitures">
      <section className="hero">
        <h1 className="hero-title">Mes voitures en location</h1>
        <p className="hero-sub">
          Ajoutez vos voitures pour qu'elles apparaissent dans les annonces
        </p>
      </section>

      <div className="mes-voitures-layout">
        {/* Formulaire d'ajout */}
        <div className="auth-card form-voiture">
          <h2 className="auth-title">
            {editingId ? "Modifier une voiture" : "Ajouter une voiture"}
          </h2>
          <form onSubmit={handleSubmit} className="auth-form">
            <div className="field">
              <label>Nom / Modele *</label>
              <input
                type="text"
                value={editingId ? editingData.nom || "" : nom}
                onChange={(e) =>
                  editingId
                    ? setEditingData({ ...editingData, nom: e.target.value })
                    : setNom(e.target.value)
                }
                placeholder="Ex: Yaris 2020"
                required
              />
            </div>
            <div className="field">
              <label>Marque *</label>
              <input
                type="text"
                value={editingId ? editingData.marque || "" : marque}
                onChange={(e) =>
                  editingId
                    ? setEditingData({ ...editingData, marque: e.target.value })
                    : setMarque(e.target.value)
                }
                placeholder="Ex: Toyota"
                required
              />
            </div>
            <div className="field">
              <label>Ville *</label>
              <input
                type="text"
                value={editingId ? editingData.ville || "" : ville}
                onChange={(e) =>
                  editingId
                    ? setEditingData({ ...editingData, ville: e.target.value })
                    : setVille(e.target.value)
                }
                placeholder="Ex: Casablanca"
                required
              />
            </div>
            <div className="field">
              <label>Prix</label>
              <input
                type="text"
                value={editingId ? editingData.prix || "" : prix}
                onChange={(e) =>
                  editingId
                    ? setEditingData({ ...editingData, prix: e.target.value })
                    : setPrix(e.target.value)
                }
                placeholder="Ex: 250 DH / jour"
              />
            </div>
            <div className="field">
              <label>Description</label>
              <textarea
                value={editingId ? editingData.description || "" : description}
                onChange={(e) =>
                  editingId
                    ? setEditingData({ ...editingData, description: e.target.value })
                    : setDescription(e.target.value)
                }
                placeholder="Couleur, etat, kilometrage, options..."
                rows="3"
              />
            </div>
            <div className="field">
              <label>Photo</label>
              <input
                id="photo-input"
                type="file"
                accept="image/*"
                onChange={(e) =>
                  editingId
                    ? setEditingData({ ...editingData, photo: e.target.files[0] })
                    : setPhoto(e.target.files[0])
                }
              />
            </div>

            <div style={{ display: "flex", gap: "10px" }}>
              <button type="submit" className="btn-primary" disabled={envoi}>
                {envoi
                  ? editingId
                    ? "Modification en cours..."
                    : "Ajout en cours..."
                  : editingId
                  ? "Modifier la voiture"
                  : "Ajouter la voiture"}
              </button>
              {editingId && (
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={annulerEdition}
                  disabled={envoi}
                  style={{
                    background: "#888",
                    color: "white",
                    padding: "12px 20px",
                    border: "none",
                    borderRadius: "4px",
                    cursor: "pointer",
                  }}
                >
                  Annuler
                </button>
              )}
            </div>
          </form>

          {message && <p className="auth-success">{message}</p>}
          {erreur && <p className="auth-error">{erreur}</p>}
        </div>

        {/* Liste des voitures du proprietaire */}
        <div className="liste-voitures">
          <h2 className="section-title">
            Mes annonces ({mesVoitures.length})
          </h2>

          {chargement && (
            <div className="loading">
              <div className="spinner"></div>
              <p>Chargement...</p>
            </div>
          )}

          {!chargement && mesVoitures.length === 0 && (
            <p className="empty-state">
              Vous n'avez pas encore ajoute de voiture. Utilisez le formulaire a
              gauche pour commencer !
            </p>
          )}

          <div className="grid">
            {mesVoitures.map((v) => (
              <article key={v.id} className="card">
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
                  <span className="source-badge source-proprio">
                    Proprietaire
                  </span>
                </div>
                <div className="card-body">
                  <h3 className="card-title">
                    {v.marque} - {v.nom}
                  </h3>
                  <div className="card-infos-obligatoires">
                    <p className="card-spec">
                      <strong>Site :</strong> Proprietaire AutoLoc
                    </p>
                    <p className="card-spec">
                      <strong>Marque :</strong> {v.marque}
                    </p>
                    <p className="card-spec">
                      <strong>Modele :</strong> {v.modele || v.nom}
                    </p>
                  </div>
                  <p className="card-meta">{v.ville}</p>
                  {v.description && (
                    <p className="card-description">{v.description}</p>
                  )}
                  <p className="card-price">{v.prix}</p>
                  <div style={{ display: "flex", gap: "10px" }}>
                    <button
                      onClick={() => commencerEdition(v)}
                      className="card-link"
                      style={{
                        background: "#4CAF50",
                        color: "white",
                        padding: "8px 12px",
                        border: "none",
                        borderRadius: "4px",
                        cursor: "pointer",
                        flex: 1,
                        textAlign: "center",
                      }}
                    >
                      ✏️ Modifier
                    </button>
                    <button
                      onClick={() => supprimer(v.id)}
                      className="card-link card-link-delete"
                      style={{
                        background: "#f44336",
                        color: "white",
                        padding: "8px 12px",
                        border: "none",
                        borderRadius: "4px",
                        cursor: "pointer",
                        flex: 1,
                        textAlign: "center",
                      }}
                    >
                      🗑️ Supprimer
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default MesVoitures;
