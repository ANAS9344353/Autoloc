"""
Serializers de l'app voitures.

Utilise les ModelSerializer de DRF pour les modeles Voiture et Reservation.
Les champs calcules (image absolue, total, nb_jours...) utilisent
SerializerMethodField.
"""
import re
from rest_framework import serializers
from .models import Voiture, Reservation


def _extraire_prix_jour(prix):
    """Extrait un montant journalier depuis un texte comme '250 DH / jour'."""
    if not prix:
        return None
    match = re.search(r'\d+(?:[.,]\d+)?', prix.replace(" ", ""))
    if not match:
        return None
    return float(match.group(0).replace(",", "."))


def _infos_contact(user):
    """Retourne les infos de contact disponibles pour un utilisateur."""
    if hasattr(user, 'personal_info'):
        return {
            "nom": user.personal_info.full_name,
            "telephone": user.personal_info.phone_number,
            "email": user.personal_info.email or user.email,
        }
    return {
        "nom": user.username,
        "telephone": "",
        "email": user.email or "",
    }


class VoitureSerializer(serializers.ModelSerializer):
    """
    Serializer du modele Voiture.
    Inclut des champs calcules pour rester compatible avec le frontend :
      - image  (URL absolue de la photo)
      - modele (= nom)
      - source (= "Proprietaire AutoLoc")
      - is_owner_listing (= True)
      - proprietaire_nom / telephone / email
    """
    image = serializers.SerializerMethodField()
    modele = serializers.SerializerMethodField()
    source = serializers.SerializerMethodField()
    is_owner_listing = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    proprietaire_nom = serializers.SerializerMethodField()
    proprietaire_telephone = serializers.SerializerMethodField()
    proprietaire_email = serializers.SerializerMethodField()

    class Meta:
        model = Voiture
        fields = [
            'id', 'nom', 'marque', 'modele', 'ville', 'description', 'prix',
            'photo', 'image', 'source', 'is_owner_listing', 'url',
            'proprietaire_nom', 'proprietaire_telephone', 'proprietaire_email',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'photo': {'write_only': True, 'required': False, 'allow_null': True},
            'description': {'required': False, 'allow_blank': True},
            'prix': {'required': False, 'allow_blank': True},
        }

    # ------- Champs calcules -------

    def get_image(self, obj):
        """URL absolue de la photo (necessite request dans le context)."""
        if not obj.photo:
            return ""
        try:
            url = obj.photo.url
            request = self.context.get('request')
            return request.build_absolute_uri(url) if request else url
        except Exception:
            return ""

    def get_modele(self, obj):
        return obj.nom

    def get_source(self, obj):
        return "Proprietaire AutoLoc"

    def get_is_owner_listing(self, obj):
        return True

    def get_url(self, obj):
        return ""  # pas d'URL externe pour les voitures proprietaires

    def get_proprietaire_nom(self, obj):
        try:
            return obj.proprietaire.personal_info.full_name
        except Exception:
            return obj.proprietaire.username

    def get_proprietaire_telephone(self, obj):
        try:
            return obj.proprietaire.personal_info.phone_number
        except Exception:
            return ""

    def get_proprietaire_email(self, obj):
        try:
            return obj.proprietaire.personal_info.email
        except Exception:
            return obj.proprietaire.email or ""

    def to_representation(self, instance):
        """Personnalise la sortie : prix par defaut, etc."""
        rep = super().to_representation(instance)
        if not rep.get('prix'):
            rep['prix'] = "Demander le prix"
        return rep


class ReservationSerializer(serializers.ModelSerializer):
    """
    Serializer du modele Reservation.
    Inclut des champs calcules : voiture_nom, nb_jours, total, infos contact.
    """
    # Champ pour la creation (le client envoie voiture_id en ecriture)
    voiture_id = serializers.IntegerField(write_only=True, required=False)

    # Champs calcules en lecture
    voiture_nom = serializers.SerializerMethodField()
    voiture_marque = serializers.SerializerMethodField()
    voiture_modele = serializers.SerializerMethodField()
    ville = serializers.SerializerMethodField()
    prix = serializers.SerializerMethodField()
    prix_jour = serializers.SerializerMethodField()
    nb_jours = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    client_nom = serializers.SerializerMethodField()
    client_email = serializers.SerializerMethodField()
    client_info = serializers.SerializerMethodField()
    proprietaire_info = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = [
            'id', 'voiture_id',
            'voiture_nom', 'voiture_marque', 'voiture_modele',
            'ville', 'prix', 'prix_jour', 'nb_jours', 'total',
            'client_nom', 'client_email', 'client_info', 'proprietaire_info',
            'date_debut', 'date_fin', 'statut', 'created_at',
        ]
        read_only_fields = ['id', 'statut', 'created_at']

    # ========== VALIDATIONS ==========

    def validate_date_debut(self, value):
        """La date de debut ne peut pas etre dans le passe."""
        from datetime import date
        if value < date.today():
            raise serializers.ValidationError(
                "La date de debut ne peut pas etre dans le passe."
            )
        return value

    def validate(self, attrs):
        """Validation globale : date_fin doit etre >= date_debut."""
        date_debut = attrs.get('date_debut')
        date_fin = attrs.get('date_fin')

        if date_debut and date_fin:
            if date_fin < date_debut:
                raise serializers.ValidationError({
                    'date_fin': "La date de fin doit etre apres la date de debut."
                })
            # Limite raisonnable : pas plus de 365 jours
            duree = (date_fin - date_debut).days + 1
            if duree > 365:
                raise serializers.ValidationError({
                    'date_fin': "La duree maximale d'une reservation est de 365 jours."
                })
        return attrs

    # ========== CHAMPS CALCULES ==========

    def get_voiture_nom(self, obj):
        return f"{obj.voiture.marque} {obj.voiture.nom}"

    def get_voiture_marque(self, obj):
        return obj.voiture.marque

    def get_voiture_modele(self, obj):
        return obj.voiture.nom

    def get_ville(self, obj):
        return obj.voiture.ville

    def get_prix(self, obj):
        return obj.voiture.prix or "Demander le prix"

    def get_prix_jour(self, obj):
        return _extraire_prix_jour(obj.voiture.prix)

    def get_nb_jours(self, obj):
        try:
            return max((obj.date_fin - obj.date_debut).days + 1, 1)
        except Exception:
            return 1

    def get_total(self, obj):
        prix_jour = _extraire_prix_jour(obj.voiture.prix)
        if prix_jour is None:
            return None
        nb = self.get_nb_jours(obj)
        return round(prix_jour * nb, 2)

    def get_client_nom(self, obj):
        return obj.client.username

    def get_client_email(self, obj):
        return obj.client.email

    def get_client_info(self, obj):
        return _infos_contact(obj.client)

    def get_proprietaire_info(self, obj):
        return _infos_contact(obj.voiture.proprietaire)
