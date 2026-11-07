"""
Views de l'app voitures.

Architecture CRUD :
============================================================
  VOITURE                                  RESERVATION
  -------                                  -----------
  CREATE : voiture_list_create POST        reservation_create POST
  READ   : voiture_list_create GET         reservation_list_proprietaire GET
           voiture_detail GET              reservation_list_client GET
           voitures_publiques GET
  UPDATE : voiture_detail PUT/PATCH        reservation_accepter PATCH
                                           reservation_rejeter PATCH
  DELETE : voiture_detail DELETE           (pas de DELETE : on rejette)
============================================================
"""
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status

from django.db import transaction

from .models import Voiture, Reservation
from .serializers import VoitureSerializer, ReservationSerializer


def _reservations_qui_chevauchent(voiture, date_debut, date_fin, statuts):
    """
    Retourne les reservations de cette voiture dont la periode chevauche
    [date_debut, date_fin] (bornes incluses) et dont le statut est dans `statuts`.

    Deux periodes se chevauchent si : debut_A <= fin_B ET fin_A >= debut_B.
    """
    return Reservation.objects.filter(
        voiture=voiture,
        statut__in=statuts,
        date_debut__lte=date_fin,
        date_fin__gte=date_debut,
    )


# ============================================================
#  HELPERS
# ============================================================
def _verifier_proprietaire(user):
    """Verifie que l'utilisateur est bien un proprietaire de voiture.
    Retourne (True, None) si OK, sinon (False, Response_erreur)."""
    try:
        info = user.personal_info
    except Exception:
        return False, Response(
            {'erreur': "Profil incomplet"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not info.is_owner:
        return False, Response(
            {'erreur': "Vous n'etes pas un proprietaire de voiture"},
            status=status.HTTP_403_FORBIDDEN,
        )
    return True, None


# ============================================================
#  CRUD - VOITURE
# ============================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def voiture_list_create(request):
    """
    GET  /api/mes-voitures/   -> READ   : liste mes voitures
    POST /api/mes-voitures/   -> CREATE : ajouter une voiture
    """
    user = request.user

    # Verifier que c'est un proprietaire
    ok, erreur = _verifier_proprietaire(user)
    if not ok:
        return erreur

    # ---- READ : liste ----
    if request.method == 'GET':
        voitures = Voiture.objects.filter(proprietaire=user)
        serializer = VoitureSerializer(
            voitures, many=True, context={'request': request}
        )
        return Response(serializer.data)

    # ---- CREATE ----
    # Validation manuelle (champs obligatoires) pour avoir un message clair
    nom = (request.data.get('nom') or '').strip()
    marque = (request.data.get('marque') or '').strip()
    ville = (request.data.get('ville') or '').strip()
    if not nom or not marque or not ville:
        return Response(
            {'erreur': 'Champs obligatoires : nom, marque, ville'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    voiture = Voiture.objects.create(
        proprietaire=user,
        nom=nom,
        marque=marque,
        ville=ville,
        description=(request.data.get('description') or '').strip(),
        prix=(request.data.get('prix') or '').strip(),
        photo=request.FILES.get('photo'),
    )
    serializer = VoitureSerializer(voiture, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def voiture_detail(request, voiture_id):
    """
    GET    /api/mes-voitures/<id>/   -> READ   : details d'une voiture
    PUT    /api/mes-voitures/<id>/   -> UPDATE : modifier (champs complets)
    PATCH  /api/mes-voitures/<id>/   -> UPDATE : modifier (partiel)
    DELETE /api/mes-voitures/<id>/   -> DELETE : supprimer
    """
    try:
        voiture = Voiture.objects.get(id=voiture_id, proprietaire=request.user)
    except Voiture.DoesNotExist:
        return Response(
            {'erreur': 'Voiture introuvable'},
            status=status.HTTP_404_NOT_FOUND,
        )

    # ---- READ : detail ----
    if request.method == 'GET':
        serializer = VoitureSerializer(voiture, context={'request': request})
        return Response(serializer.data)

    # ---- DELETE ----
    if request.method == 'DELETE':
        voiture.delete()
        return Response({'message': 'Voiture supprimee'})

    # ---- UPDATE (PUT / PATCH) ----
    nom = (request.data.get('nom') or voiture.nom).strip()
    marque = (request.data.get('marque') or voiture.marque).strip()
    ville = (request.data.get('ville') or voiture.ville).strip()

    if not nom or not marque or not ville:
        return Response(
            {'erreur': 'Champs obligatoires : nom, marque, ville'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    voiture.nom = nom
    voiture.marque = marque
    voiture.ville = ville
    voiture.description = (request.data.get('description') or voiture.description or '').strip()
    voiture.prix = (request.data.get('prix') or voiture.prix or '').strip()

    photo = request.FILES.get('photo')
    if photo:
        voiture.photo = photo

    voiture.save()

    serializer = VoitureSerializer(voiture, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def voitures_publiques(request):
    """
    GET /api/voitures-proprietaires/  -> READ public : toutes les voitures
    proprietaires (utilise pour la liste publique cote frontend).

    Supporte la pagination optionnelle via les query params :
      ?page=1&page_size=20

    Sans query param "page", renvoie une liste plate (compatibilite frontend).
    Avec "?page=N", renvoie un objet pagine {count, next, previous, results}.
    """
    voitures = Voiture.objects.all()

    # Si l'utilisateur demande une page specifique, on pagine
    if 'page' in request.query_params:
        from rest_framework.pagination import PageNumberPagination

        paginator = PageNumberPagination()
        paginator.page_size = 20
        paginator.page_size_query_param = 'page_size'
        paginator.max_page_size = 100

        page = paginator.paginate_queryset(voitures, request)
        serializer = VoitureSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    # Sinon, comportement classique : liste plate
    serializer = VoitureSerializer(
        voitures, many=True, context={'request': request}
    )
    return Response(serializer.data)


# ============================================================
#  CRUD - RESERVATION
# ============================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reservation_create(request):
    """
    POST /api/reservations/  -> CREATE : creer une demande de reservation

    Valide les donnees via ReservationSerializer (dates dans le futur,
    date_fin >= date_debut, duree <= 365 jours).
    """
    voiture_id = request.data.get('voiture_id')

    if not voiture_id:
        return Response(
            {'erreur': 'Champ obligatoire : voiture_id'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        voiture = Voiture.objects.get(id=voiture_id)
    except Voiture.DoesNotExist:
        return Response(
            {'erreur': 'Voiture introuvable'},
            status=status.HTTP_404_NOT_FOUND,
        )

    # On ne peut pas reserver sa propre voiture
    if voiture.proprietaire == request.user:
        return Response(
            {'erreur': 'Vous ne pouvez pas reserver votre propre voiture'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validation via le serializer (verifie les dates : passe, ordre, duree max)
    serializer = ReservationSerializer(data=request.data)
    if not serializer.is_valid():
        # Recuperer un message d'erreur lisible
        errors = serializer.errors
        first_field = next(iter(errors))
        first_msg = errors[first_field]
        if isinstance(first_msg, list) and first_msg:
            first_msg = str(first_msg[0])
        return Response(
            {'erreur': str(first_msg)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    date_debut = serializer.validated_data['date_debut']
    date_fin = serializer.validated_data['date_fin']

    # La voiture ne doit pas deja etre reservee (reservation acceptee) sur ces dates
    conflit = _reservations_qui_chevauchent(
        voiture, date_debut, date_fin, ['ACCEPTEE']
    ).order_by('date_debut').first()
    if conflit:
        return Response(
            {'erreur': (
                f'Cette voiture est deja reservee du '
                f'{conflit.date_debut:%d/%m/%Y} au {conflit.date_fin:%d/%m/%Y}'
            )},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Le meme client ne peut pas envoyer deux demandes en attente sur les memes dates
    if _reservations_qui_chevauchent(
        voiture, date_debut, date_fin, ['PENDING']
    ).filter(client=request.user).exists():
        return Response(
            {'erreur': 'Vous avez deja une demande en attente pour cette voiture sur ces dates'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Creation effective (la validation est passee)
    try:
        reservation = Reservation.objects.create(
            voiture=voiture,
            client=request.user,
            date_debut=serializer.validated_data['date_debut'],
            date_fin=serializer.validated_data['date_fin'],
        )
        # Recharger depuis la BDD pour que date_debut/date_fin soient des
        # objets date() (et pas des chaines) -> calcul correct de nb_jours/total
        reservation.refresh_from_db()
    except Exception as e:
        return Response(
            {'erreur': str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    out = ReservationSerializer(reservation)
    return Response(out.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reservation_list_proprietaire(request):
    """
    GET /api/mes-reservations-proprietaire/
    READ : toutes les demandes recues sur les voitures du proprietaire connecte.
    """
    voitures = Voiture.objects.filter(proprietaire=request.user)
    reservations = Reservation.objects.filter(voiture__in=voitures)
    serializer = ReservationSerializer(reservations, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reservation_list_client(request):
    """
    GET /api/mes-reservations-client/
    READ : toutes les reservations faites par le client connecte.
    """
    reservations = Reservation.objects.filter(client=request.user)
    serializer = ReservationSerializer(reservations, many=True)
    return Response(serializer.data)


def _changer_statut(request, reservation_id, nouveau_statut):
    """Helper : change le statut d'une reservation (ACCEPTEE ou REJETEE)."""
    try:
        reservation = Reservation.objects.get(id=reservation_id)
    except Reservation.DoesNotExist:
        return Response(
            {'erreur': 'Reservation introuvable'},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Seul le proprietaire de la voiture peut accepter / rejeter
    if reservation.voiture.proprietaire != request.user:
        return Response(
            {'erreur': 'Non autorise'},
            status=status.HTTP_403_FORBIDDEN,
        )

    if reservation.statut != 'PENDING':
        return Response(
            {'erreur': f'Cette reservation est deja {reservation.statut}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if nouveau_statut != 'ACCEPTEE':
        reservation.statut = nouveau_statut
        reservation.save()
        return Response(ReservationSerializer(reservation).data)

    # Acceptation : verrouiller la voiture pour eviter que deux acceptations
    # simultanees reservent les memes dates.
    with transaction.atomic():
        Voiture.objects.select_for_update().get(pk=reservation.voiture_id)

        conflit = _reservations_qui_chevauchent(
            reservation.voiture, reservation.date_debut, reservation.date_fin, ['ACCEPTEE']
        ).exclude(pk=reservation.pk).order_by('date_debut').first()
        if conflit:
            return Response(
                {'erreur': (
                    f'Impossible d\'accepter : la voiture est deja reservee du '
                    f'{conflit.date_debut:%d/%m/%Y} au {conflit.date_fin:%d/%m/%Y}'
                )},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reservation.statut = 'ACCEPTEE'
        reservation.save()

        # Les autres demandes en attente sur les memes dates ne peuvent plus
        # etre satisfaites : elles sont rejetees automatiquement.
        _reservations_qui_chevauchent(
            reservation.voiture, reservation.date_debut, reservation.date_fin, ['PENDING']
        ).exclude(pk=reservation.pk).update(statut='REJETEE')

    return Response(ReservationSerializer(reservation).data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def reservation_accepter(request, reservation_id):
    """PATCH /api/reservations/<id>/accepter/  -> UPDATE : statut = ACCEPTEE"""
    return _changer_statut(request, reservation_id, 'ACCEPTEE')


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def reservation_rejeter(request, reservation_id):
    """PATCH /api/reservations/<id>/rejeter/  -> UPDATE : statut = REJETEE"""
    return _changer_statut(request, reservation_id, 'REJETEE')
