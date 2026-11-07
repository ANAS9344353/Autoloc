"""
Views de l'app accounts.

Authentification par JWT (JSON Web Token) via djangorestframework-simplejwt.
A chaque connexion on renvoie un token "access" (courte duree) et un token "refresh".
"""
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import SignupSerializer, LoginSerializer


def _generer_tokens_jwt(user):
    """Genere un couple (access, refresh) JWT pour un utilisateur."""
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


def _premiere_erreur(errors):
    """Recupere le premier message d'erreur d'un dictionnaire d'erreurs DRF."""
    if not errors:
        return "Donnees invalides"
    first_field = next(iter(errors))
    first = errors[first_field]
    if isinstance(first, list) and first:
        return str(first[0])
    return str(first)


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    """Inscription : cree le User + PersonalInfo et retourne un JWT."""
    serializer = SignupSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'erreur': _premiere_erreur(serializer.errors)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = serializer.save()
    tokens = _generer_tokens_jwt(user)

    return Response({
        'token': tokens['access'],       # le frontend utilise "token" comme nom de cle
        'refresh': tokens['refresh'],
        'username': user.personal_info.full_name,
        'is_owner': user.personal_info.is_owner,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Connexion : verifie email/password et retourne un JWT."""
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'erreur': 'Email et mot de passe requis'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    email = serializer.validated_data['email']
    password = serializer.validated_data['password']

    # On utilise l'email comme username
    user = authenticate(username=email, password=password)
    if user is None:
        return Response(
            {'erreur': 'Email ou mot de passe incorrect'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    tokens = _generer_tokens_jwt(user)

    # Recuperer les infos du profil (le front a besoin de is_owner)
    full_name = email
    is_owner = False
    try:
        info = user.personal_info
        full_name = info.full_name
        is_owner = info.is_owner
    except Exception:
        pass

    return Response({
        'token': tokens['access'],
        'refresh': tokens['refresh'],
        'username': full_name,
        'is_owner': is_owner,
    })
