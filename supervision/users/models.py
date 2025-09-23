from django.db import models

# Create your models here.
class Zone(models.Model):
    nom_zone = models.CharField(max_length=70)


class Chef(models.Model):
    nom = models.CharField(max_length=80)
    prenom = models.CharField(max_length=125)
    email = models.CharField(max_length=100)
    zone = models.OneToOneField(Zone, on_delete=models.CASCADE)

class Auditeur(models.Model):
    nom = models.CharField(max_length=80)
    prenom = models.CharField(max_length=125)
    email = models.CharField(max_length=100)
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='zones')


class Authentification(models.Model):
    identifiant = models.CharField(max_length=20)
    password = models.CharField(max_length=15)
    role = models.CharField(max_length=50)