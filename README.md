# AutoLoc — Location de voitures au Maroc

Application full-stack de location de voitures avec :

- **Backend** : Django 4 + Django REST Framework
- **Authentification** : **JWT** (JSON Web Token) via `djangorestframework-simplejwt`
- **Base de donnees** : **MySQL** (accessible via phpMyAdmin / XAMPP)
- **Frontend** : React 18 + **Vite** (remplace Create React App)
- **Sources** : voitures scrapees depuis Avito.ma, Moteur.ma, MarocAnnonces.com + voitures ajoutees par les proprietaires inscrits

---

## Stack technique - resume

| Composant | Technologie |
|---|---|
| Framework backend | Django 4.2+ |
| API REST | Django REST Framework |
| **Authentification** | **JWT** (`djangorestframework-simplejwt`) |
| Serializers | **DRF `ModelSerializer`** (pas de serialisation manuelle) |
| Base de donnees | **MySQL** via XAMPP / phpMyAdmin |
| Driver MySQL | PyMySQL (Python pur) |
| Frontend | React 18 |
| **Bundler frontend** | **Vite** (pas Create React App) |
| Scraping | requests + BeautifulSoup |
| CORS | django-cors-headers |

---

## Lancement rapide (resume)

### Etape 1 - Demarrer MySQL via XAMPP
1. Lancer XAMPP -> Start Apache + Start MySQL
2. http://localhost/phpmyadmin -> Creer la base `autoloc_db` (utf8mb4)

### Etape 2 - Backend Django
```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser     # (optionnel - pour l'admin)
python manage.py runserver
```
-> http://127.0.0.1:8000

### Etape 3 - Frontend React + Vite
Dans un autre terminal :
```bash
cd frontend
npm install
npm run dev
```
-> http://127.0.0.1:3000

---

## Voir et editer la base dans phpMyAdmin

- http://localhost/phpmyadmin
- Cliquer sur `autoloc_db`
- Tables visibles :
  - `auth_user` (utilisateurs Django)
  - `accounts_personalinfo` (infos perso + flag is_owner)
  - `voitures_voiture` (les voitures des proprietaires)
  - `voitures_reservation` (les reservations)
  - Tables systeme Django (`auth_group`, `django_admin_log`, etc.)
  - Tables JWT (`token_blacklist_*`) si on active la blacklist

---

## Architecture CRUD complete

### CRUD Voiture (modele principal)

| Operation | Methode HTTP | URL | Fonction view |
|---|---|---|---|
| **C**reate | POST | `/api/mes-voitures/` | `voiture_list_create` |
| **R**ead (liste) | GET | `/api/mes-voitures/` | `voiture_list_create` |
| **R**ead (detail) | GET | `/api/mes-voitures/<id>/` | `voiture_detail` |
| **R**ead (public) | GET | `/api/voitures-proprietaires/` | `voitures_publiques` |
| **U**pdate | PUT / PATCH | `/api/mes-voitures/<id>/` | `voiture_detail` |
| **D**elete | DELETE | `/api/mes-voitures/<id>/` | `voiture_detail` |

### CRUD Reservation

| Operation | Methode | URL | Fonction view |
|---|---|---|---|
| **C**reate | POST | `/api/reservations/` | `reservation_create` |
| **R**ead (recues) | GET | `/api/mes-reservations-proprietaire/` | `reservation_list_proprietaire` |
| **R**ead (envoyees) | GET | `/api/mes-reservations-client/` | `reservation_list_client` |
| **U**pdate (accepter) | PATCH | `/api/reservations/<id>/accepter/` | `reservation_accepter` |
| **U**pdate (rejeter) | PATCH | `/api/reservations/<id>/rejeter/` | `reservation_rejeter` |

---

## Authentification JWT

### Inscription
```http
POST /api/signup/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "monMdp",
  "full_name": "Jean Dupont",
  "phone_number": "0612345678",
  "is_owner": true
}
```
Reponse :
```json
{
  "token": "eyJhbGc...",        // access token JWT
  "refresh": "eyJhbGc...",      // refresh token JWT
  "username": "Jean Dupont",
  "is_owner": true
}
```

### Connexion
```http
POST /api/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "monMdp"
}
```

### Utiliser le token dans les requetes protegees
```http
GET /api/mes-voitures/
Authorization: Bearer eyJhbGc...
```

### Rafraichir un token expire
```http
POST /api/token/refresh/
Content-Type: application/json

{ "refresh": "eyJhbGc..." }
```

---

## Structure du projet

```
location_voitures_finales/
├── README.md                          ← ce fichier
├── backend/                           ← Django + DRF + JWT + MySQL
│   ├── README.md                      ← guide backend detaille
│   ├── manage.py
│   ├── requirements.txt
│   ├── backend/
│   │   ├── __init__.py                ← charge PyMySQL
│   │   ├── settings.py                ← MySQL + JWT
│   │   ├── urls.py
│   │   └── views.py
│   ├── accounts/
│   │   ├── models.py                  ← PersonalInfo
│   │   ├── serializers.py             ← *** NOUVEAU : SignupSerializer, LoginSerializer ***
│   │   ├── views.py                   ← signup, login (JWT)
│   │   └── urls.py
│   ├── voitures/
│   │   ├── models.py                  ← Voiture, Reservation
│   │   ├── serializers.py             ← *** NOUVEAU : VoitureSerializer, ReservationSerializer ***
│   │   ├── views.py                   ← CRUD complet structure proprement
│   │   └── urls.py
│   └── scraper/
│       ├── scraper.py
│       ├── views.py                   ← utilise VoitureSerializer
│       └── urls.py
└── frontend/                          ← React + Vite
    ├── README.md                      ← guide frontend detaille
    ├── package.json                   ← dependances Vite (pas react-scripts)
    ├── vite.config.js                 ← configuration Vite
    ├── index.html                     ← a la racine (convention Vite)
    └── src/
        ├── main.jsx                   ← point d'entree (ex index.js)
        ├── App.jsx
        ├── Login.jsx
        ├── Signup.jsx
        ├── Voitures.jsx
        ├── MesVoitures.jsx
        ├── MesReservations.jsx
        └── App.css
```

---

## Differences avec la version precedente

| Element | Ancien | Nouveau |
|---|---|---|
| Authentification | Token DRF (table `authtoken_token`) | **JWT** (JSON Web Token signe) |
| Header HTTP | `Authorization: Token xxx` | `Authorization: Bearer xxx` |
| Frontend bundler | Create React App (react-scripts) | **Vite** |
| Entree frontend | `src/index.js` | `src/main.jsx` |
| Extensions fichiers | `.js` | `.jsx` |
| Commande dev | `npm start` | `npm run dev` (ou `npm start`) |
| Serialisation | Fonctions manuelles | **DRF Serializers (`ModelSerializer`)** |
| Base de donnees | SQLite (fichier local) | **MySQL via phpMyAdmin** |

---

## Points cles a retenir pour la soutenance

1. **JWT** : Le token est signe cryptographiquement. Il contient l'`user_id` et expire au bout de 7 jours. Verifiable sans acceder a la base.
2. **Serializers** : Tous les modeles ont leur classe `Serializer` qui gere validation + conversion JSON.
3. **CRUD** : Les operations sont separees proprement (`voiture_list_create` pour CREATE+READ list, `voiture_detail` pour READ+UPDATE+DELETE).
4. **MySQL** : Base reelle, visible et editable dans phpMyAdmin.
5. **Vite** : Bundler moderne, demarrage instantane, HMR natif.
6. **Pas de double reservation** : une demande est refusee si ses dates chevauchent une reservation deja acceptee pour la meme voiture. Quand le proprietaire accepte une demande, les autres demandes en attente sur les memes dates sont rejetees automatiquement (verrou `select_for_update` dans une transaction pour eviter deux acceptations simultanees).
