from django.urls import path
from . import views

urlpatterns = [
    # =========== CRUD VOITURE ===========
    # CREATE + READ liste
    path('mes-voitures/', views.voiture_list_create, name='voiture_list_create'),
    # READ detail + UPDATE + DELETE
    path('mes-voitures/<int:voiture_id>/', views.voiture_detail, name='voiture_detail'),
    # READ public
    path('voitures-proprietaires/', views.voitures_publiques, name='voitures_publiques'),

    # =========== CRUD RESERVATION ===========
    # CREATE
    path('reservations/', views.reservation_create, name='reservation_create'),
    # READ
    path('mes-reservations-proprietaire/', views.reservation_list_proprietaire,
         name='reservation_list_proprietaire'),
    path('mes-reservations-client/', views.reservation_list_client,
         name='reservation_list_client'),
    # UPDATE (changement de statut)
    path('reservations/<int:reservation_id>/accepter/', views.reservation_accepter,
         name='reservation_accepter'),
    path('reservations/<int:reservation_id>/rejeter/', views.reservation_rejeter,
         name='reservation_rejeter'),
]
