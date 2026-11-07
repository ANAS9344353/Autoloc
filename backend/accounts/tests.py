"""
Tests unitaires de l'app accounts.

Pour lancer ces tests :
    python manage.py test accounts
    python manage.py test accounts -v 2   (mode verbeux)
"""
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from .models import PersonalInfo
from .serializers import SignupSerializer, LoginSerializer


# ================================================================
#  TESTS DU MODELE PersonalInfo
# ================================================================
class PersonalInfoModelTests(TestCase):
    """Tests du modele PersonalInfo."""

    def test_creation_personal_info(self):
        """On peut creer un PersonalInfo lie a un User."""
        user = User.objects.create_user('jean@x.com', 'jean@x.com', 'pass')
        info = PersonalInfo.objects.create(
            user=user,
            email='jean@x.com',
            full_name='Jean Dupont',
            phone_number='0612345678',
            is_owner=True,
        )
        self.assertEqual(info.full_name, 'Jean Dupont')
        self.assertEqual(info.user, user)
        self.assertTrue(info.is_owner)

    def test_relation_user_personal_info(self):
        """On peut acceder a PersonalInfo via user.personal_info."""
        user = User.objects.create_user('m@x.com', 'm@x.com', 'pass')
        PersonalInfo.objects.create(
            user=user, email='m@x.com', full_name='M',
            phone_number='0611111111', is_owner=False,
        )
        self.assertEqual(user.personal_info.full_name, 'M')

    def test_is_owner_par_defaut_false(self):
        """Par defaut, is_owner doit etre False."""
        user = User.objects.create_user('a@x.com', 'a@x.com', 'pass')
        info = PersonalInfo.objects.create(
            user=user, email='a@x.com', full_name='A', phone_number='0600000000',
        )
        self.assertFalse(info.is_owner)


# ================================================================
#  TESTS DU SERIALIZER Signup
# ================================================================
class SignupSerializerTests(TestCase):
    """Tests du serializer Signup (validation)."""

    def test_signup_valide(self):
        """Donnees valides : le serializer est valide."""
        data = {
            'email': 'nouveau@x.com', 'password': 'password123',
            'full_name': 'Test', 'phone_number': '0612345678', 'is_owner': True,
        }
        s = SignupSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)

    def test_signup_email_invalide(self):
        """Email mal forme : rejete."""
        data = {
            'email': 'pas-un-email', 'password': 'pass',
            'full_name': 'X', 'phone_number': '0600000000',
        }
        s = SignupSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('email', s.errors)

    def test_signup_telephone_trop_court(self):
        """Telephone < 10 chiffres : rejete."""
        data = {
            'email': 'a@x.com', 'password': 'password',
            'full_name': 'X', 'phone_number': '0612',
        }
        s = SignupSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('phone_number', s.errors)

    def test_signup_telephone_non_numerique(self):
        """Telephone avec lettres : rejete."""
        data = {
            'email': 'a@x.com', 'password': 'password',
            'full_name': 'X', 'phone_number': 'abcdefghij',
        }
        s = SignupSerializer(data=data)
        self.assertFalse(s.is_valid())

    def test_signup_email_duplique(self):
        """Email deja en BDD : rejete."""
        User.objects.create_user('a@x.com', 'a@x.com', 'pass')
        data = {
            'email': 'a@x.com', 'password': 'password',
            'full_name': 'X', 'phone_number': '0612345678',
        }
        s = SignupSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('email', s.errors)

    def test_signup_password_trop_court(self):
        """Password < 4 caracteres : rejete."""
        data = {
            'email': 'a@x.com', 'password': 'a',
            'full_name': 'X', 'phone_number': '0612345678',
        }
        s = SignupSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('password', s.errors)

    def test_signup_create_method(self):
        """La methode create() cree bien User + PersonalInfo."""
        data = {
            'email': 'new@x.com', 'password': 'password',
            'full_name': 'New User', 'phone_number': '0612345678', 'is_owner': True,
        }
        s = SignupSerializer(data=data)
        self.assertTrue(s.is_valid())
        user = s.save()
        self.assertEqual(user.email, 'new@x.com')
        self.assertTrue(hasattr(user, 'personal_info'))
        self.assertEqual(user.personal_info.full_name, 'New User')
        self.assertTrue(user.personal_info.is_owner)


# ================================================================
#  TESTS DES ENDPOINTS API (signup, login)
# ================================================================
class SignupEndpointTests(TestCase):
    """Tests de l'endpoint POST /api/signup/."""

    def setUp(self):
        self.client = APIClient()

    def test_signup_retourne_jwt(self):
        """Un signup reussi renvoie un access et un refresh JWT."""
        r = self.client.post('/api/signup/', {
            'email': 'a@x.com', 'password': 'password',
            'full_name': 'A', 'phone_number': '0612345678', 'is_owner': True,
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn('token', r.data)
        self.assertIn('refresh', r.data)
        self.assertTrue(r.data['token'].startswith('eyJ'))

    def test_signup_cree_user_et_personalinfo(self):
        """Un signup cree bien un User ET un PersonalInfo en BDD."""
        self.client.post('/api/signup/', {
            'email': 'b@x.com', 'password': 'password',
            'full_name': 'B', 'phone_number': '0611111111', 'is_owner': False,
        }, format='json')
        self.assertTrue(User.objects.filter(email='b@x.com').exists())
        user = User.objects.get(email='b@x.com')
        self.assertEqual(user.personal_info.full_name, 'B')

    def test_signup_email_duplique_renvoie_400(self):
        """Tentative d'inscription avec email existant : 400."""
        self.client.post('/api/signup/', {
            'email': 'c@x.com', 'password': 'password',
            'full_name': 'C', 'phone_number': '0612345678',
        }, format='json')
        r = self.client.post('/api/signup/', {
            'email': 'c@x.com', 'password': 'password',
            'full_name': 'D', 'phone_number': '0612345678',
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)


class LoginEndpointTests(TestCase):
    """Tests de l'endpoint POST /api/login/."""

    def setUp(self):
        self.client = APIClient()
        # Creer un utilisateur de test
        self.client.post('/api/signup/', {
            'email': 'user@x.com', 'password': 'monpass',
            'full_name': 'User', 'phone_number': '0612345678', 'is_owner': True,
        }, format='json')

    def test_login_valide(self):
        """Login avec bons credentials : 200 + JWT."""
        r = self.client.post('/api/login/', {
            'email': 'user@x.com', 'password': 'monpass',
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn('token', r.data)
        self.assertIn('refresh', r.data)
        self.assertEqual(r.data['username'], 'User')
        self.assertTrue(r.data['is_owner'])

    def test_login_mauvais_password(self):
        """Login avec mauvais password : 400."""
        r = self.client.post('/api/login/', {
            'email': 'user@x.com', 'password': 'mauvais',
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_user_inexistant(self):
        """Login avec email inconnu : 400."""
        r = self.client.post('/api/login/', {
            'email': 'inconnu@x.com', 'password': 'pass',
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)


class JWTEndpointsTests(TestCase):
    """Tests des endpoints JWT (refresh, verify)."""

    def setUp(self):
        self.client = APIClient()
        r = self.client.post('/api/signup/', {
            'email': 'jwt@x.com', 'password': 'pass',
            'full_name': 'JWT', 'phone_number': '0612345678',
        }, format='json')
        self.access = r.data['token']
        self.refresh = r.data['refresh']

    def test_token_refresh(self):
        """POST /api/token/refresh/ avec un refresh valide renvoie un nouveau access."""
        r = self.client.post('/api/token/refresh/',
                             {'refresh': self.refresh}, format='json')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn('access', r.data)
        self.assertTrue(r.data['access'].startswith('eyJ'))

    def test_token_verify_valide(self):
        """POST /api/token/verify/ avec un token valide : 200."""
        r = self.client.post('/api/token/verify/',
                             {'token': self.access}, format='json')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_token_verify_invalide(self):
        """POST /api/token/verify/ avec un token invalide : 401."""
        r = self.client.post('/api/token/verify/',
                             {'token': 'invalid.token.here'}, format='json')
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)
