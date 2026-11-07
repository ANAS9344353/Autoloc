from django.urls import path
from . import views

urlpatterns = [
    path('liste-voitures/', views.liste_voitures),
]
