"""
Configuration de l'interface d'administration Django pour l'app voitures.

Accessible via http://127.0.0.1:8000/admin/ apres avoir cree un super-utilisateur
avec : python manage.py createsuperuser

Permet de :
 - Voir / ajouter / modifier / supprimer toutes les voitures
 - Voir / accepter / rejeter / supprimer toutes les reservations
 - Filtrer et rechercher facilement
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Voiture, Reservation


@admin.register(Voiture)
class VoitureAdmin(admin.ModelAdmin):
    """Gestion des voitures dans l'admin."""

    # Colonnes affichees dans la liste
    list_display = (
        'id', 'nom', 'marque', 'ville', 'prix',
        'proprietaire', 'apercu_photo', 'created_at',
    )

    # Filtres a droite
    list_filter = ('marque', 'ville', 'created_at')

    # Recherche en haut
    search_fields = ('nom', 'marque', 'ville', 'description',
                     'proprietaire__username', 'proprietaire__email')

    # Liens cliquables
    list_display_links = ('id', 'nom')

    # Tri par defaut
    ordering = ('-created_at',)

    # Champs en lecture seule
    readonly_fields = ('created_at',)

    # Organisation du formulaire de detail
    fieldsets = (
        ('Informations principales', {
            'fields': ('proprietaire', 'nom', 'marque', 'ville', 'prix')
        }),
        ('Description et photo', {
            'fields': ('description', 'photo'),
        }),
        ('Metadonnees', {
            'fields': ('created_at',),
            'classes': ('collapse',),    # section repliee par defaut
        }),
    )

    def apercu_photo(self, obj):
        """Petite vignette de la photo dans la liste."""
        if obj.photo:
            return format_html(
                '<img src="{}" style="height:40px;border-radius:4px;" />',
                obj.photo.url,
            )
        return "—"
    apercu_photo.short_description = "Photo"


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """Gestion des reservations dans l'admin."""

    list_display = (
        'id', 'voiture', 'client',
        'date_debut', 'date_fin', 'statut_colore', 'created_at',
    )

    list_filter = ('statut', 'date_debut', 'created_at')

    search_fields = (
        'voiture__nom', 'voiture__marque',
        'client__username', 'client__email',
    )

    list_display_links = ('id', 'voiture')

    ordering = ('-created_at',)

    readonly_fields = ('created_at',)

    # Permet de modifier le statut directement depuis la liste
    list_editable = ('date_debut', 'date_fin')

    # Actions personnalisees dans le menu deroulant
    actions = ['accepter_selection', 'rejeter_selection']

    def statut_colore(self, obj):
        """Affiche le statut avec une couleur pour le voir d'un coup d'oeil."""
        couleurs = {
            'PENDING':  ('#f59e0b', 'En attente'),
            'ACCEPTEE': ('#10b981', 'Acceptee'),
            'REJETEE':  ('#ef4444', 'Rejetee'),
        }
        couleur, texte = couleurs.get(obj.statut, ('#666', obj.statut))
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;'
            'border-radius:12px;font-weight:600;font-size:11px;">{}</span>',
            couleur, texte,
        )
    statut_colore.short_description = "Statut"

    def accepter_selection(self, request, queryset):
        """Action groupee : accepter toutes les reservations selectionnees."""
        nb = queryset.update(statut='ACCEPTEE')
        self.message_user(request, f"{nb} reservation(s) acceptee(s).")
    accepter_selection.short_description = "Accepter les reservations selectionnees"

    def rejeter_selection(self, request, queryset):
        """Action groupee : rejeter toutes les reservations selectionnees."""
        nb = queryset.update(statut='REJETEE')
        self.message_user(request, f"{nb} reservation(s) rejetee(s).")
    rejeter_selection.short_description = "Rejeter les reservations selectionnees"
