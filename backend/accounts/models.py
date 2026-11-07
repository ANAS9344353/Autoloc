from django.db import models
from django.contrib.auth.models import User


class PersonalInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='personal_info')
    email = models.EmailField()
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    is_owner = models.BooleanField(default=False)  # True si proprietaire de voiture
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.user.username}"
