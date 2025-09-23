from django.db import models

# Create your models here.
class Fichiers(models.Model):
    nom_fichier = models.CharField(max_length=255)
    type_mime = models.CharField(max_length=100, null=True, blank=True)
    contenu = models.BinaryField()
    date_ajout = models.DateTimeField(auto_now_add=True)


    # def __str__(self) -> str:
    #     return self.nom_fichier