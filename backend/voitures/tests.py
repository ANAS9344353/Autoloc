"""
Tests unitaires de l'app voitures.

Couvre :
 - Modeles Voiture et Reservation
 - Serializers (champs calcules + validations)
 - Endpoints CRUD complets
 - Securite (un user ne peut pas toucher aux donnees d'un autre)

Pour lancer ces tests :
    python manage.py test voitures
    python manage.py test voitures -v 2   (mode verbeux)
"""
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import PersonalInfo
from .models import Voiture, Reservation
from .serializers import VoitureSerializer, ReservationSerializer


# ================================================================
#  HELPERS
# ================================================================
def _creer_user(email='u@x.com', password='pass', is_owner=False, full_name='User'):
    """Cree un User avec son PersonalInfo associe."""
    user = User.objects.create_user(email, email, password)
    PersonalInfo.objects.create(
        user=user, email=email, full_name=full_name,
        phone_number='0612345678', is_owner=is_owner,
    )
    return user


def _get_jwt_token(client, email, password):
    """Connecte un user et retourne son access token."""
    r = client.post('/api/login/',
                    {'email': email, 'password': password}, format='json')
    return r.data['token']


# ================================================================
#  TESTS DU MODELE Voiture
# ================================================================
class VoitureModelTests(TestCase):

    def setUp(self):
        self.owner = _creer_user('o@x.com', 'pass', is_owner=True)

    def test_creation_voiture(self):
        """On peut creer une voiture."""
        v = Voiture.objects.create(
            proprietaire=self.owner, nom='Yaris', marque='Toyota',
            ville='Casablanca', prix='200 DH / jour',
        )
        self.assertEqual(v.nom, 'Yaris')
        self.assertEqual(v.proprietaire, self.owner)

    def test_relation_user_voitures(self):
        """user.voitures retourne toutes les voitures du user."""
        Voiture.objects.create(proprietaire=self.owner, nom='V1', marque='M', ville='C')
        Voiture.objects.create(proprietaire=self.owner, nom='V2', marque='M', ville='C')
        self.assertEqual(self.owner.voitures.count(), 2)

    def test_ordering_par_date_creation(self):
        """Les voitures sont triees par date de creation (desc)."""
        v1 = Voiture.objects.create(proprietaire=self.owner, nom='V1', marque='M', ville='C')
        v2 = Voiture.objects.create(proprietaire=self.owner, nom='V2', marque='M', ville='C')
        voitures = list(Voiture.objects.all())
        self.assertEqual(voitures[0], v2)  # le plus recent en premier


# ================================================================
#  TESTS DU SERIALIZER Voiture
# ================================================================
class VoitureSerializerTests(TestCase):

    def setUp(self):
        self.owner = _creer_user('o@x.com', 'pass', is_owner=True, full_name='Jean')
        self.voiture = Voiture.objects.create(
            proprietaire=self.owner, nom='Clio', marque='Renault',
            ville='Rabat', prix='180 DH / jour',
        )

    def test_serializer_retourne_tous_les_champs(self):
        """Le serializer retourne bien tous les champs attendus."""
        data = VoitureSerializer(self.voiture).data
        attendus = ['id', 'nom', 'marque', 'modele', 'ville', 'prix',
                    'image', 'source', 'is_owner_listing',
                    'proprietaire_nom', 'proprietaire_telephone', 'proprietaire_email']
        for champ in attendus:
            self.assertIn(champ, data, f"Le champ {champ} manque")

    def test_source_est_proprietaire_autoloc(self):
        """Le champ source est toujours 'Proprietaire AutoLoc'."""
        data = VoitureSerializer(self.voiture).data
        self.assertEqual(data['source'], 'Proprietaire AutoLoc')

    def test_proprietaire_nom_correct(self):
        """proprietaire_nom retourne le full_name du PersonalInfo."""
        data = VoitureSerializer(self.voiture).data
        self.assertEqual(data['proprietaire_nom'], 'Jean')

    def test_modele_egale_nom(self):
        """Le champ modele est un alias de nom."""
        data = VoitureSerializer(self.voiture).data
        self.assertEqual(data['modele'], self.voiture.nom)

    def test_prix_par_defaut_si_vide(self):
        """Si prix vide, on affiche 'Demander le prix'."""
        v = Voiture.objects.create(proprietaire=self.owner, nom='V', marque='M', ville='C')
        data = VoitureSerializer(v).data
        self.assertEqual(data['prix'], 'Demander le prix')


# ================================================================
#  TESTS DU SERIALIZER Reservation (validations strictes)
# ================================================================
class ReservationSerializerValidationTests(TestCase):

    def test_date_debut_passee_rejetee(self):
        """date_debut dans le passe est rejetee."""
        s = ReservationSerializer(data={
            'date_debut': str(date.today() - timedelta(days=5)),
            'date_fin': str(date.today() - timedelta(days=2)),
        })
        self.assertFalse(s.is_valid())
        self.assertIn('date_debut', s.errors)

    def test_date_fin_avant_date_debut_rejetee(self):
        """date_fin < date_debut est rejetee."""
        s = ReservationSerializer(data={
            'date_debut': str(date.today() + timedelta(days=10)),
            'date_fin':   str(date.today() + timedelta(days=5)),
        })
        self.assertFalse(s.is_valid())

    def test_duree_superieure_a_365_rejetee(self):
        """Reservation > 365 jours rejetee."""
        s = ReservationSerializer(data={
            'date_debut': str(date.today() + timedelta(days=1)),
            'date_fin':   str(date.today() + timedelta(days=400)),
        })
        self.assertFalse(s.is_valid())

    def test_dates_valides_acceptees(self):
        """Dates valides : OK."""
        s = ReservationSerializer(data={
            'date_debut': str(date.today() + timedelta(days=1)),
            'date_fin':   str(date.today() + timedelta(days=5)),
        })
        self.assertTrue(s.is_valid(), s.errors)

    def test_date_aujourdhui_acceptee(self):
        """Reserver pour aujourd'hui meme : OK (pas dans le passe)."""
        s = ReservationSerializer(data={
            'date_debut': str(date.today()),
            'date_fin':   str(date.today() + timedelta(days=2)),
        })
        self.assertTrue(s.is_valid(), s.errors)


# ================================================================
#  TESTS CRUD VOITURE (endpoints)
# ================================================================
class VoitureCRUDTests(TestCase):
    """Tests des endpoints CRUD sur les voitures (authentifies par JWT)."""

    def setUp(self):
        self.owner = _creer_user('o@x.com', 'pass', is_owner=True)
        self.client_user = _creer_user('c@x.com', 'pass', is_owner=False)
        self.api = APIClient()
        self.token_owner = _get_jwt_token(self.api, 'o@x.com', 'pass')
        self.token_client = _get_jwt_token(self.api, 'c@x.com', 'pass')

    # --- CREATE ---
    def test_create_voiture(self):
        """POST /api/mes-voitures/ cree une voiture."""
        self.api.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token_owner)
        r = self.api.post('/api/mes-voitures/', {
            'nom': 'Yaris', 'marque': 'Toyota', 'ville': 'Casablanca',
            'prix': '200 DH / jour',
        }, format='multipart')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data['nom'], 'Yaris')

    def test_create_sans_jwt_refuse(self):
        """Sans JWT, POST -> 401."""
        r = self.api.post('/api/mes-voitures/', {
            'nom': 'X', 'marque': 'Y', 'ville': 'Z',
        }, format='multipart')
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_non_proprietaire_refuse(self):
        """Un user non-proprietaire ne peut pas creer une voiture (403)."""
        self.api.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token_client)
        r = self.api.post('/api/mes-voitures/', {
            'nom': 'X', 'marque': 'Y', 'ville': 'Z',
        }, format='multipart')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_sans_champs_obligatoires(self):
        """Si nom/marque/ville manque -> 400."""
        self.api.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token_owner)
        r = self.api.post('/api/mes-voitures/', {'nom': 'X'}, format='multipart')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    # --- READ ---
    def test_read_liste_mes_voitures(self):
        """GET /api/mes-voitures/ retourne mes voitures."""
        Voiture.objects.create(proprietaire=self.owner, nom='V1', marque='M', ville='C')
        Voiture.objects.create(proprietaire=self.owner, nom='V2', marque='M', ville='C')
        self.api.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token_owner)
        r = self.api.get('/api/mes-voitures/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 2)

    def test_read_detail_voiture(self):
        """GET /api/mes-voitures/<id>/ retourne le detail."""
        v = Voiture.objects.create(proprietaire=self.owner, nom='V', marque='M', ville='C')
        self.api.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token_owner)
        r = self.api.get(f'/api/mes-voitures/{v.id}/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['nom'], 'V')

    def test_read_publique_sans_auth(self):
        """GET /api/voitures-proprietaires/ : accessible sans auth."""
        Voiture.objects.create(proprietaire=self.owner, nom='V', marque='M', ville='C')
        r = self.api.get('/api/voitures-proprietaires/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(r.data), 1)

    # --- UPDATE ---
    def test_update_voiture(self):
        """PUT /api/mes-voitures/<id>/ modifie une voiture."""
        v = Voiture.objects.create(proprietaire=self.owner, nom='V', marque='M', ville='C', prix='100')
        self.api.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token_owner)
        r = self.api.put(f'/api/mes-voitures/{v.id}/', {
            'nom': 'NEW', 'marque': 'NEW', 'ville': 'NEW', 'prix': '999',
        }, format='multipart')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['nom'], 'NEW')

    # --- DELETE ---
    def test_delete_voiture(self):
        """DELETE /api/mes-voitures/<id>/ supprime."""
        v = Voiture.objects.create(proprietaire=self.owner, nom='V', marque='M', ville='C')
        self.api.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token_owner)
        r = self.api.delete(f'/api/mes-voitures/{v.id}/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertFalse(Voiture.objects.filter(id=v.id).exists())

    # --- SECURITE ---
    def test_securite_ne_voir_que_ses_voitures(self):
        """Un proprietaire ne voit pas les voitures d'un autre proprietaire."""
        other = _creer_user('other@x.com', 'pass', is_owner=True)
        Voiture.objects.create(proprietaire=other, nom='Autre', marque='M', ville='C')

        self.api.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token_owner)
        r = self.api.get('/api/mes-voitures/')
        self.assertEqual(len(r.data), 0)   # je ne vois pas les voitures de other

    def test_securite_ne_peut_pas_modifier_autre(self):
        """Un user ne peut pas modifier la voiture d'un autre user."""
        other = _creer_user('other2@x.com', 'pass', is_owner=True)
        v = Voiture.objects.create(proprietaire=other, nom='Autre', marque='M', ville='C')

        self.api.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token_owner)
        r = self.api.delete(f'/api/mes-voitures/{v.id}/')
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)


# ================================================================
#  TESTS CRUD RESERVATION
# ================================================================
class ReservationCRUDTests(TestCase):

    def setUp(self):
        self.owner = _creer_user('o@x.com', 'pass', is_owner=True)
        self.client_user = _creer_user('c@x.com', 'pass', is_owner=False)
        self.voiture = Voiture.objects.create(
            proprietaire=self.owner, nom='V', marque='M', ville='C', prix='100 DH / jour',
        )
        self.api = APIClient()
        self.token_owner = _get_jwt_token(self.api, 'o@x.com', 'pass')
        self.token_client = _get_jwt_token(self.api, 'c@x.com', 'pass')

    def test_create_reservation(self):
        """POST /api/reservations/ cree une demande."""
        self.api.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token_client)
        r = self.api.post('/api/reservations/', {
            'voiture_id': self.voiture.id,
            'date_debut': str(date.today() + timedelta(days=5)),
            'date_fin':   str(date.today() + timedelta(days=8)),
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data['statut'], 'PENDING')
        self.assertEqual(r.data['nb_jours'], 4)
        self.assertEqual(r.data['total'], 400.0)

    def test_create_reservation_validation_dates_passees(self):
        """date_debut dans le passe : 400."""
        self.api.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token_client)
        r = self.api.post('/api/reservations/', {
            'voiture_id': self.voiture.id,
            'date_debut': str(date.today() - timedelta(days=5)),
            'date_fin':   str(date.today() - timedelta(days=2)),
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_reservation_dates_inversees(self):
        """date_fin < date_debut : 400."""
        self.api.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token_client)
        r = self.api.post('/api/reservations/', {
            'voiture_id': self.voiture.id,
            'date_debut': str(date.today() + timedelta(days=10)),
            'date_fin':   str(date.today() + timedelta(days=5)),
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_proprietaire_ne_peut_pas_reserver_sa_voiture(self):
        """Le proprietaire ne peut pas reserver sa propre voiture."""
        self.api.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token_owner)
        r = self.api.post('/api/reservations/', {
            'voiture_id': self.voiture.id,
            'date_debut': str(date.today() + timedelta(days=5)),
            'date_fin':   str(date.today() + timedelta(days=8)),
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_proprietaire_voit_les_demandes_recues(self):
        """GET /api/mes-reservations-proprietaire/ liste les demandes recues."""
        Reservation.objects.create(
            voiture=self.voiture, client=self.client_user,
            date_debut=date.today() + timedelta(days=1),
            date_fin=date.today() + timedelta(days=3),
        )
        self.api.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token_owner)
        r = self.api.get('/api/mes-reservations-proprietaire/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 1)

    def test_client_voit_ses_demandes_envoyees(self):
        """GET /api/mes-reservations-client/ liste les demandes envoyees."""
        Reservation.objects.create(
            voiture=self.voiture, client=self.client_user,
            date_debut=date.today() + timedelta(days=1),
            date_fin=date.today() + timedelta(days=3),
        )
        self.api.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token_client)
        r = self.api.get('/api/mes-reservations-client/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 1)

    def test_accepter_reservation(self):
        """PATCH /api/reservations/<id>/accepter/ change le statut."""
        res = Reservation.objects.create(
            voiture=self.voiture, client=self.client_user,
            date_debut=date.today() + timedelta(days=1),
            date_fin=date.today() + timedelta(days=3),
        )
        self.api.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token_owner)
        r = self.api.patch(f'/api/reservations/{res.id}/accepter/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        res.refresh_from_db()
        self.assertEqual(res.statut, 'ACCEPTEE')

    def test_rejeter_reservation(self):
        """PATCH /api/reservations/<id>/rejeter/ change le statut."""
        res = Reservation.objects.create(
            voiture=self.voiture, client=self.client_user,
            date_debut=date.today() + timedelta(days=1),
            date_fin=date.today() + timedelta(days=3),
        )
        self.api.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token_owner)
        r = self.api.patch(f'/api/reservations/{res.id}/rejeter/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        res.refresh_from_db()
        self.assertEqual(res.statut, 'REJETEE')

    def test_client_ne_peut_pas_accepter(self):
        """Le client ne peut pas accepter sa propre reservation (403)."""
        res = Reservation.objects.create(
            voiture=self.voiture, client=self.client_user,
            date_debut=date.today() + timedelta(days=1),
            date_fin=date.today() + timedelta(days=3),
        )
        self.api.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token_client)
        r = self.api.patch(f'/api/reservations/{res.id}/accepter/')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
