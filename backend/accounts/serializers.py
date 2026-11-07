"""
Serializers de l'app accounts.

Utilise les classes Serializer de Django REST Framework pour :
 - Valider les donnees envoyees par le frontend
 - Convertir les modeles Python en JSON
 - Convertir le JSON en instances de modeles
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import PersonalInfo


class PersonalInfoSerializer(serializers.ModelSerializer):
    """Serializer du modele PersonalInfo (lecture seule des infos perso)."""

    class Meta:
        model = PersonalInfo
        fields = ['id', 'email', 'full_name', 'phone_number', 'is_owner', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer du modele User (avec les infos perso liees)."""
    personal_info = PersonalInfoSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'personal_info']


class SignupSerializer(serializers.Serializer):
    """
    Serializer pour la creation d'un compte.
    Centralise toute la validation (email, password, telephone, doublon...).
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=4)
    full_name = serializers.CharField(max_length=100)
    phone_number = serializers.CharField(max_length=20)
    is_owner = serializers.BooleanField(default=False, required=False)

    def validate_email(self, value):
        if '@' not in value:
            raise serializers.ValidationError('Email invalide (doit contenir @)')
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email deja utilise')
        return value

    def validate_phone_number(self, value):
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError(
                'Le numero de telephone doit contenir exactement 10 chiffres'
            )
        return value

    def create(self, validated_data):
        # 1. Creer le User Django (mot de passe hashe automatiquement)
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        # 2. Creer les infos perso liees
        PersonalInfo.objects.create(
            user=user,
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            phone_number=validated_data['phone_number'],
            is_owner=validated_data.get('is_owner', False),
        )
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer pour la connexion (email + mot de passe)."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
