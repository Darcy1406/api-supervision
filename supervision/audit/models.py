from django.db import models
from django.conf import settings

class AuditLog(models.Model):
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL,
        null=True
    )
    action = models.CharField(max_length=255)
    modele = models.CharField(max_length=255)
    objet_id = models.CharField(max_length=50, null=True, blank=True)
    document_filename = models.CharField(max_length=255, null=True, blank=True)
    ancienne_valeur = models.JSONField(null=True, blank=True)
    nouvelle_valeur = models.JSONField(null=True, blank=True)
    date_action = models.DateTimeField(auto_now_add=True)
    adresse_ip = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.utilisateur} - {self.action} sur {self.modele} ({self.objet_id})"