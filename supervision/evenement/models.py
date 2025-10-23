from django.db import models
from users.models import Utilisateur

# Create your models here.
class Agenda(models.Model):
    # role_user = models.CharField(max_length=50)
    # id_user = models.IntegerField()
    description = models.CharField(max_length=255)
    date_evenement = models.DateField()
    heure_evenement = models.TimeField()
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name="evenements", null=True)

     