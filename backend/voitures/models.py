from django.db import models
from django.contrib.auth.models import User


class Voiture(models.Model):
    proprietaire = models.ForeignKey(User, on_delete=models.CASCADE, related_name='voitures')
    nom = models.CharField(max_length=100)
    marque = models.CharField(max_length=80)
    ville = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    prix = models.CharField(max_length=50, blank=True, help_text="Ex: 250 DH / jour")
    photo = models.ImageField(upload_to='voitures/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.marque} {self.nom} - {self.proprietaire.username}"


class Reservation(models.Model):
    STATUT_CHOICES = [
        ('PENDING', 'En attente'),
        ('ACCEPTEE', 'Acceptée'),
        ('REJETEE', 'Rejetée'),
    ]
    
    voiture = models.ForeignKey(Voiture, on_delete=models.CASCADE, related_name='reservations')
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mes_reservations')
    date_debut = models.DateField()
    date_fin = models.DateField()
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Reservation {self.id} - {self.voiture} par {self.client.username}"
