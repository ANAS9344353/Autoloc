# Backend AutoLoc - Django + DRF + JWT + MySQL

## Pile technique

| Couche | Outil |
|---|---|
| Framework Web | Django 4.2+ |
| API REST | Django REST Framework |
| Authentification | **JWT** via `djangorestframework-simplejwt` |
| Base de donnees | **MySQL** (via XAMPP / phpMyAdmin) |
| Driver MySQL | PyMySQL (Python pur, pas besoin de compiler) |
| Scraping | requests + BeautifulSoup |

## Prerequis

1. **Python 3.9 ou plus** installe.
2. **XAMPP installe** (Apache + MySQL en service).
3. (Optionnel) un environnement virtuel Python.

## Etape 1 - Creer la base de donnees dans phpMyAdmin

1. Demarrer XAMPP, puis cliquer sur **Start** pour Apache **ET** MySQL.
2. Ouvrir un navigateur sur : http://localhost/phpmyadmin
3. Cliquer sur **"Nouvelle base de donnees"** dans le menu de gauche.
4. Nom : `autoloc_db`
5. Interclassement : `utf8mb4_unicode_ci`
6. Cliquer sur **Creer**.

C'est tout pour la BDD. Les tables seront creees automatiquement par les migrations Django a l'etape suivante.

## Etape 2 - Installer les dependances Python

```bash
# 1. Aller dans le dossier backend
cd backend

# 2. (Optionnel mais recommande) Creer un environnement virtuel
python -m venv venv

# Activer le venv :
#   Windows  : venv\Scripts\activate
#   Linux/Mac: source venv/bin/activate

# 3. Installer les paquets
pip install -r requirements.txt
```

Contenu de `requirements.txt` :
```
Django>=4.2,<5.1
djangorestframework
djangorestframework-simplejwt
django-cors-headers
requests
beautifulsoup4
Pillow
PyMySQL
cryptography
```

## Etape 3 - Appliquer les migrations (cree les tables MySQL)

```bash
python manage.py makemigrations
python manage.py migrate
```

Resultat : tu verras dans phpMyAdmin les tables creees dans `autoloc_db` :
- `auth_user`, `auth_group`, `auth_permission`, ...
- `accounts_personalinfo`
- `voitures_voiture`
- `voitures_reservation`
- `token_blacklist_*` (pour JWT, optionnel)
- etc.

## Etape 4 - Creer un super-utilisateur (pour /admin/)

```bash
python manage.py createsuperuser
```

Renseigner : username, email, mot de passe.

### Interface d'administration Django

Une fois le super-utilisateur cree, l'interface d'administration est accessible sur :
**http://127.0.0.1:8000/admin/**

Elle permet de :
- Voir et gerer tous les utilisateurs (`auth_user`)
- Voir et gerer les infos perso (`PersonalInfo`)
- Ajouter / modifier / supprimer toutes les voitures (`Voiture`)
- Voir, accepter, rejeter ou supprimer les reservations (`Reservation`)
- Rechercher et filtrer par marque, ville, statut, date...
- Effectuer des actions groupees (accepter / rejeter plusieurs reservations a la fois)

Configuration de l'admin dans :
- `accounts/admin.py` (PersonalInfoAdmin)
- `voitures/admin.py` (VoitureAdmin, ReservationAdmin)

## Etape 5 - Lancer le serveur

```bash
python manage.py runserver
```

Le backend tourne sur : http://127.0.0.1:8000/

- Page d'accueil    : http://127.0.0.1:8000/
- Liste endpoints   : http://127.0.0.1:8000/api/
- Interface admin   : http://127.0.0.1:8000/admin/

## Configuration par variables d'environnement (.env)

Les valeurs sensibles (SECRET_KEY, mot de passe MySQL, JWT) sont
lues depuis un fichier `.env` grace a la librairie `python-dotenv`.

1. Un fichier `.env.example` sert de modele (commite dans Git).
2. Le vrai fichier `.env` contient les valeurs locales (exclu de Git).
3. Pour configurer un nouveau poste : `cp .env.example .env` puis editer `.env`.

Variables disponibles : `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`,
`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`,
`JWT_ACCESS_LIFETIME_DAYS`, `JWT_REFRESH_LIFETIME_DAYS`.

## Lancer les tests automatises

Le projet contient **67 tests unitaires** repartis dans 3 apps :

```bash
# Lancer TOUS les tests
python manage.py test

# Mode verbeux (voir chaque test)
python manage.py test -v 2

# Tester une app precise
python manage.py test accounts
python manage.py test voitures
python manage.py test scraper
```

Les tests couvrent :
- Les modeles (creation, relations, contraintes)
- Les serializers (validation email/telephone/dates)
- Tous les endpoints CRUD (create, read, update, delete)
- L'authentification JWT (signup, login, refresh, verify)
- La securite (un user ne peut pas modifier les donnees d'un autre)
- Le scraper (extraction marque/ville/prix, fusion avec la BDD)

> Note : Django cree automatiquement une base de test temporaire
> (`test_autoloc_db`) et la detruit a la fin. Ta base `autoloc_db`
> n'est jamais touchee par les tests.

## Endpoints API

### Authentification (JWT)

| Methode | URL | Description |
|---|---|---|
| POST | `/api/signup/` | Inscription. Retourne `{token, refresh, username, is_owner}` |
| POST | `/api/login/` | Connexion. Retourne `{token, refresh, username, is_owner}` |
| POST | `/api/token/refresh/` | Rafraichir l'access token via le refresh token |
| POST | `/api/token/verify/` | Verifier un token |

### Voitures (CRUD)

| Methode | URL | Auth | Description |
|---|---|---|---|
| GET    | `/api/mes-voitures/` | JWT | READ - liste mes voitures |
| POST   | `/api/mes-voitures/` | JWT | CREATE - ajouter une voiture |
| GET    | `/api/mes-voitures/<id>/` | JWT | READ - detail d'une voiture |
| PUT    | `/api/mes-voitures/<id>/` | JWT | UPDATE - modifier (complet) |
| PATCH  | `/api/mes-voitures/<id>/` | JWT | UPDATE - modifier (partiel) |
| DELETE | `/api/mes-voitures/<id>/` | JWT | DELETE - supprimer |
| GET    | `/api/voitures-proprietaires/` | - | Liste publique |
| GET    | `/api/liste-voitures/` | - | Liste fusionnee (scraping + propros) |

### Reservations

| Methode | URL | Auth | Description |
|---|---|---|---|
| POST   | `/api/reservations/` | JWT | CREATE |
| GET    | `/api/mes-reservations-proprietaire/` | JWT | READ (cote proprietaire) |
| GET    | `/api/mes-reservations-client/` | JWT | READ (cote client) |
| PATCH  | `/api/reservations/<id>/accepter/` | JWT | UPDATE statut -> ACCEPTEE |
| PATCH  | `/api/reservations/<id>/rejeter/` | JWT | UPDATE statut -> REJETEE |

## Authentification JWT - comment ca marche

1. Le client envoie POST `/api/login/` avec `email` + `password`.
2. Le serveur repond `{"token": "eyJhbGc...", "refresh": "eyJhbGc..."}`.
3. Le client envoie ce token dans le header :
   ```
   Authorization: Bearer eyJhbGc...
   ```
4. Quand l'access token expire (7 jours par defaut), le client utilise le refresh token :
   ```
   POST /api/token/refresh/
   Body: { "refresh": "eyJhbGc..." }
   ```
   Le serveur renvoie un nouveau access token.

## Architecture du code

```
backend/
├── manage.py
├── requirements.txt
├── backend/                ← App de configuration
│   ├── __init__.py         ← Charge PyMySQL
│   ├── settings.py         ← MySQL + JWT + DRF
│   ├── urls.py             ← URLs racine
│   └── views.py            ← Pages d'accueil HTML
├── accounts/               ← Inscription / Connexion
│   ├── models.py           ← PersonalInfo
│   ├── serializers.py      ← SignupSerializer, LoginSerializer, UserSerializer
│   ├── views.py            ← signup, login (JWT)
│   └── urls.py
├── voitures/               ← Voitures + Reservations
│   ├── models.py           ← Voiture, Reservation
│   ├── serializers.py      ← VoitureSerializer, ReservationSerializer
│   ├── views.py            ← CRUD complet (list/create, detail, public)
│   └── urls.py
└── scraper/                ← Scraping de sites externes
    ├── scraper.py
    ├── views.py            ← /api/liste-voitures (utilise VoitureSerializer)
    └── urls.py
```

## Verifier dans phpMyAdmin

1. Aller sur http://localhost/phpmyadmin
2. Cliquer sur la base `autoloc_db`.
3. Tu vois toutes les tables : `auth_user`, `accounts_personalinfo`, `voitures_voiture`, `voitures_reservation`, etc.
4. Cliquer sur une table pour voir / modifier les donnees directement.

## Probleme courant : "django.db.utils.OperationalError"

Causes possibles :
- MySQL n'est pas demarre dans XAMPP -> Demarrer le service.
- Base `autoloc_db` non creee -> La creer dans phpMyAdmin.
- Mot de passe MySQL non vide -> Modifier `DATABASES > PASSWORD` dans `backend/settings.py`.

## Probleme : "django.core.exceptions.ImproperlyConfigured: ... mysqlclient"

Si Django demande `mysqlclient` au lieu de PyMySQL : verifier que `backend/__init__.py`
contient bien :
```python
import pymysql
pymysql.install_as_MySQLdb()
```
