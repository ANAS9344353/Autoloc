"""
Tests unitaires de l'app scraper.

On NE teste PAS le scraping reel (qui depend du reseau et des sites
externes Avito/Moteur/MarocAnnonces). On teste les fonctions internes
d'extraction (marque, ville, prix) et l'endpoint /api/liste-voitures/.

Pour lancer ces tests :
    python manage.py test scraper
"""
from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import PersonalInfo
from voitures.models import Voiture
from .scraper import (
    _extraire_marque_modele,
    _extraire_ville,
    _extraire_prix,
    _nettoyer_titre,
)


# ================================================================
#  TESTS DES FONCTIONS D'EXTRACTION (logique pure, pas de reseau)
# ================================================================
class ExtractionMarqueTests(TestCase):
    """Tests de la fonction _extraire_marque_modele."""

    def test_marque_directe_dans_titre(self):
        """Si le titre contient la marque, on l'extrait."""
        marque, modele = _extraire_marque_modele("Renault Clio 5 a louer")
        self.assertEqual(marque, "Renault")

    def test_marque_devinee_depuis_modele(self):
        """Si le titre ne contient que le modele, on devine la marque."""
        marque, modele = _extraire_marque_modele("CLIO 5 LOCATION CASA")
        self.assertEqual(marque, "Renault")

    def test_marque_toyota_yaris(self):
        """Yaris -> Toyota."""
        marque, modele = _extraire_marque_modele("Yaris 2022 disponible")
        self.assertEqual(marque, "Toyota")

    def test_marque_inconnue(self):
        """Si rien n'est reconnu, la marque peut etre vide ou generique."""
        marque, modele = _extraire_marque_modele("Voiture a louer pas cher")
        # On verifie juste que ca ne plante pas
        self.assertIsInstance(marque, str)


class ExtractionVilleTests(TestCase):
    """Tests de la fonction _extraire_ville."""

    def test_ville_casablanca(self):
        ville = _extraire_ville("Belle voiture a Casablanca a louer")
        self.assertEqual(ville, "Casablanca")

    def test_ville_rabat(self):
        ville = _extraire_ville("Location a Rabat centre")
        self.assertEqual(ville, "Rabat")

    def test_ville_marrakech(self):
        ville = _extraire_ville("Voiture Marrakech disponible")
        self.assertEqual(ville, "Marrakech")

    def test_ville_inconnue_retourne_defaut(self):
        """Si pas de ville reconnue, retourne une valeur par defaut (pas d'erreur)."""
        ville = _extraire_ville("Texte sans ville connue")
        self.assertIsInstance(ville, str)


class ExtractionPrixTests(TestCase):
    """Tests de la fonction _extraire_prix."""

    def test_prix_avec_dh(self):
        prix = _extraire_prix("Location a 250 DH par jour")
        self.assertIn("250", prix)

    def test_prix_sans_montant(self):
        """Si pas de prix, retourne une chaine (pas d'erreur)."""
        prix = _extraire_prix("Voiture a louer, contactez-nous")
        self.assertIsInstance(prix, str)


class NettoyageTitreTests(TestCase):
    """Tests de la fonction _nettoyer_titre."""

    def test_nettoyer_espaces(self):
        titre = _nettoyer_titre("  Renault   Clio  ")
        self.assertEqual(titre, "Renault Clio")

    def test_nettoyer_titre_vide(self):
        titre = _nettoyer_titre("")
        self.assertEqual(titre, "")


# ================================================================
#  TEST DE L'ENDPOINT /api/liste-voitures/ (scraper mocke)
# ================================================================
class ListeVoituresEndpointTests(TestCase):
    """
    Tests de l'endpoint /api/liste-voitures/.
    On MOCKE scraper_locations() pour ne pas dependre du reseau.
    """

    def setUp(self):
        self.api = APIClient()
        # Creer un proprietaire avec une voiture
        owner = User.objects.create_user('o@x.com', 'o@x.com', 'pass')
        PersonalInfo.objects.create(
            user=owner, email='o@x.com', full_name='Owner',
            phone_number='0612345678', is_owner=True,
        )
        Voiture.objects.create(
            proprietaire=owner, nom='Yaris', marque='Toyota',
            ville='Casablanca', prix='200 DH / jour',
        )

    @patch('scraper.views.scraper_locations')
    def test_liste_voitures_sans_scraper(self, mock_scraper):
        """Sans resultat scraper, on retourne quand meme les voitures BDD."""
        mock_scraper.return_value = []
        r = self.api.get('/api/liste-voitures/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(r.data), 1)
        # La premiere voiture doit etre une voiture proprietaire
        self.assertEqual(r.data[0]['source'], 'Proprietaire AutoLoc')

    @patch('scraper.views.scraper_locations')
    def test_liste_voitures_avec_scraper(self, mock_scraper):
        """Les voitures scrapees sont fusionnees avec les voitures BDD."""
        mock_scraper.return_value = [
            {'nom': 'Externe', 'marque': 'BMW', 'ville': 'Rabat',
             'prix': '500 DH', 'image': '', 'source': 'Avito.ma'},
        ]
        r = self.api.get('/api/liste-voitures/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        # Au moins 2 : 1 proprietaire + 1 externe
        self.assertGreaterEqual(len(r.data), 2)
        sources = [v.get('source') for v in r.data]
        self.assertIn('Proprietaire AutoLoc', sources)
        self.assertIn('Avito.ma', sources)

    @patch('scraper.views.scraper_locations')
    def test_voitures_proprietaires_en_premier(self, mock_scraper):
        """Les voitures proprietaires sont affichees AVANT les scrapees."""
        mock_scraper.return_value = [
            {'nom': 'Externe', 'marque': 'BMW', 'ville': 'Rabat',
             'prix': '500 DH', 'image': '', 'source': 'Avito.ma'},
        ]
        r = self.api.get('/api/liste-voitures/')
        self.assertEqual(r.data[0]['source'], 'Proprietaire AutoLoc')
