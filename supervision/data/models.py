from django.db import models
from users.models import Poste_comptable

# Create your models here.
class Piece(models.Model):
    nom_piece = models.CharField(max_length=10)
    periode = models.CharField(max_length=15)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    poste_comptable = models.ManyToManyField(Poste_comptable, related_name="pieces")


class Document(models.Model):
    exercice = models.CharField(max_length=10, null=True)
    mois = models.CharField(max_length=2, null=True)
    nom_fichier = models.CharField(max_length=255)
    type = models.CharField(max_length=100, null=True, blank=True)
    contenu = models.BinaryField()
    date_arrivee = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    poste_comptable = models.ForeignKey(Poste_comptable, on_delete=models.CASCADE, related_name='poste_comptable_documents')
    piece = models.ForeignKey(Piece, on_delete=models.CASCADE, related_name='piece_documents')



class Proprietaire(models.Model):
    nom_proprietaire = models.CharField(max_length=35) 


class Compte(models.Model):
    classe = models.IntegerField(default=0)
    poste = models.IntegerField(default=0)
    rubrique = models.IntegerField(default=0)
    numero = models.CharField(max_length=20)
    libelle = models.CharField(max_length=255)
    acte_reglementaire = models.CharField(max_length=255, default="")
    solde_en_cours_exo = models.CharField(max_length=35, default="")
    solde_fin_gest = models.CharField(max_length=35, default="")
    type = models.CharField(max_length=25)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    # compte_regroupement = models.ForeignKey("self", on_delete=models.CASCADE, related_name="compte_regoupes", null=True)
    proprietaire = models.ForeignKey(Proprietaire, on_delete=models.CASCADE, related_name="comptes" , null=True)


class Transcription(models.Model):
    # exercice = models.IntegerField()
    # mois = models.IntegerField()
    # date = models.DateField()
    # piece = models.CharField(max_length=40)
    compte = models.ForeignKey(Compte, on_delete=models.CASCADE, related_name='transcriptions',null=True)
    nature = models.CharField(max_length=255)
    montant = models.IntegerField()
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='documents')


    # def __str__(self) -> str:
    #     return self.nom_fichier


class PieceCompte(models.Model):
    piece = models.ForeignKey(Piece, on_delete=models.CASCADE, related_name='liaison_comptes')
    compte = models.ForeignKey(Compte, on_delete=models.CASCADE, related_name='liaison_piece')
    nature = models.CharField(max_length=255, null=True)
    created_at = models.DateField(auto_now_add=True, null=True)
    updated_at = models.DateField(auto_now=True, null=True)