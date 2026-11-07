# Frontend AutoLoc - React + Vite

## Pile technique

| Couche | Outil |
|---|---|
| Framework | React 18 |
| Bundler / Dev server | **Vite** (remplace Create React App) |
| Authentification | JWT (header `Authorization: Bearer ...`) |

## Prerequis

- **Node.js 18 ou plus** installe.

## Installation

```bash
cd frontend
npm install
```

Cela installe React, ReactDOM, Vite et @vitejs/plugin-react.

## Lancer le serveur de developpement

```bash
npm run dev
# ou son alias :
npm start
```

Le frontend tourne sur : http://127.0.0.1:3000/

Vite ouvre automatiquement le navigateur et active le **Hot Module Replacement (HMR)** :
toute modification d'un fichier `.jsx` ou `.css` est appliquee instantanement sans recharger.

## Build de production

```bash
npm run build
```

Genere le dossier `dist/` avec les fichiers optimises.

```bash
npm run preview
```

Permet de tester le build localement.

## Structure des fichiers

```
frontend/
├── index.html          ← Template HTML (a la racine, convention Vite)
├── vite.config.js      ← Configuration Vite
├── package.json
└── src/
    ├── main.jsx        ← Point d'entree (anciennement index.js)
    ├── App.jsx         ← Navigation principale
    ├── Login.jsx       ← Page connexion
    ├── Signup.jsx      ← Page inscription
    ├── Voitures.jsx    ← Liste publique + reservation
    ├── MesVoitures.jsx ← CRUD voitures (proprietaire)
    ├── MesReservations.jsx ← Gestion des reservations
    └── App.css         ← Styles
```

## Differences avec Create React App

| Aspect | Create React App | **Vite** |
|---|---|---|
| Commande dev | `npm start` | `npm run dev` (ou `npm start`) |
| Bundler | Webpack | esbuild (dev) + Rollup (build) |
| Entree HTML | `public/index.html` | `index.html` a la racine |
| Entree JS | `src/index.js` | `src/main.jsx` |
| Variables env | `REACT_APP_*` | `VITE_*` (acces via `import.meta.env`) |
| Demarrage | Lent (10s+) | **Tres rapide (<1s)** |
| HMR | Webpack-dev-server | Natif ES modules |

## Comment ca communique avec le backend ?

Toutes les requetes pointent vers `http://localhost:8000` (Django).

L'authentification utilise **JWT** :
```javascript
fetch("http://localhost:8000/api/mes-voitures/", {
  headers: { Authorization: `Bearer ${token}` }
})
```

Le token est stocke dans `localStorage` apres login/signup.

## Modifier les textes / boutons

Tous les textes affiches a l'utilisateur sont en dur dans les fichiers `.jsx` :

| Texte / bouton | Fichier |
|---|---|
| Logo "AutoLoc" | `App.jsx` |
| Liens de navigation | `App.jsx` |
| Bouton "Se connecter" | `Login.jsx` |
| Bouton "Creer mon compte" | `Signup.jsx` |
| Bouton "Reserver / Contacter" | `Voitures.jsx` |
| Boutons "Modifier" / "Supprimer" | `MesVoitures.jsx` |
| Boutons "Accepter" / "Rejeter" | `MesReservations.jsx` |
| Titre onglet navigateur | `index.html` |
| Styles (couleurs, mise en page) | `src/App.css` |

Grace au HMR de Vite, modifier un fichier et sauvegarder met a jour la page
instantanement.
