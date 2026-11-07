from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .scraper import scraper_locations
from voitures.models import Voiture
from voitures.serializers import VoitureSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def liste_voitures(request):
    """
    GET /api/liste-voitures/

    Liste fusionnee :
      - voitures des proprietaires (BDD locale, serialisees via VoitureSerializer)
      - voitures scrapees depuis Avito.ma, Moteur.ma, MarocAnnonces.com

    Les voitures proprietaires sont affichees en premier (mise en avant).
    """
    # Voitures des proprietaires (depuis MySQL)
    voitures_proprios_qs = Voiture.objects.all()
    voitures_proprios = VoitureSerializer(
        voitures_proprios_qs, many=True, context={'request': request}
    ).data

    # Voitures scrapees (dictionnaires Python, deja au bon format)
    voitures_externes = scraper_locations()

    # Fusion : proprietaires en premier
    donnees = list(voitures_proprios) + list(voitures_externes)
    return Response(donnees)
