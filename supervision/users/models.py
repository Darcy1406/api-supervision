from django.db import models
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

# Create your models here.
class Zone(models.Model):
    nom_zone = models.CharField(max_length=50)


class Utilisateur(models.Model):
    nom = models.CharField(max_length=80)
    prenom = models.CharField(max_length=128)
    email = models.CharField(max_length=100)
    fonction = models.CharField(max_length=30, null=True)
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='zones' , null=True)
    

class Poste_comptable(models.Model):
    code_poste = models.CharField(max_length=25, null=True)
    nom_poste = models.CharField(max_length=50, null=True)
    responsable = models.CharField(max_length=50, null=True)
    poste = models.CharField(max_length=50, null=True)
    lieu = models.CharField(max_length=50)
    comptable_rattachement = models.ForeignKey("self", on_delete=models.SET_NULL, related_name="poste_rattaches", null=True)
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='poste_comptables', null=True)


class AuthentificationManager(BaseUserManager):
    def create_user(self, identifiant, password=None, **extra_fields):
        if not identifiant:
            raise ValueError("L'identifiant est obligatoire")
        user = self.model(identifiant=identifiant, **extra_fields)
        user.set_password(password)  # Hash du mot de passe
        user.save(using=self._db)
        return user

    def create_superuser(self, identifiant, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(identifiant, password, **extra_fields)


class Authentification(AbstractBaseUser, PermissionsMixin):
    identifiant = models.CharField(max_length=20, unique=True)
    date_joined = models.DateTimeField(auto_now_add=True, null=True)
    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, null=True, blank=True, related_name="authentification")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = AuthentificationManager()

    # Obligatoire pour Django
    USERNAME_FIELD = "identifiant"   # champ utilisé pour se connecter
    REQUIRED_FIELDS = []             # champs obligatoires pour createsuperuser

    def __str__(self):
        return self.identifiant
