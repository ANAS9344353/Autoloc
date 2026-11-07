"""
Configuration de l'interface d'administration Django pour l'app accounts.

Accessible via http://127.0.0.1:8000/admin/ apres avoir cree un super-utilisateur
avec : python manage.py createsuperuser
"""
from django.contrib import admin
from .models import PersonalInfo


@admin.register(PersonalInfo)
class PersonalInfoAdmin(admin.ModelAdmin):
    """Affichage et gestion des infos perso dans l'admin."""

    # Colonnes affichees dans la liste
    list_display = ('id', 'full_name', 'email', 'phone_number', 'is_owner', 'created_at')

    # Filtres dans la barre laterale droite
    list_filter = ('is_owner', 'created_at')

    # Champ de recherche en haut
    search_fields = ('full_name', 'email', 'phone_number', 'user__username')

    # Liens cliquables vers le detail
    list_display_links = ('id', 'full_name')

    # Ordre par defaut (du plus recent au plus ancien)
    ordering = ('-created_at',)

    # Champs en lecture seule dans le formulaire de detail
    readonly_fields = ('created_at',)
