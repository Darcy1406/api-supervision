# from django.db.models.signals import post_save, post_delete
# from django.dispatch import receiver
# from django.forms.models import model_to_dict
# from audit.models import AuditLog
# from audit.middleware import get_current_user, get_current_request
# from datetime import datetime, date, time
# from decimal import Decimal
# from django.db.models import Model, QuerySet
# from django.db.models.fields.files import FieldFile
# from django.utils.timezone import is_aware
# from uuid import UUID
# import logging

# # 🔥 Import des modèles associés aux documents
# from data.models import Document, Transcription, Anomalie, Correction

# logger = logging.getLogger(__name__)


# # ----------------------------------------
# # 🔧 UTILITAIRES
# # ----------------------------------------

# def get_client_ip(request):
#     """Retourne l'adresse IP du client"""
#     if request is None:
#         return None

#     x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
#     if x_forwarded_for:
#         return x_forwarded_for.split(",")[0]

#     return request.META.get("REMOTE_ADDR")


# def serialize_value(value):
#     """Sérialise correctement les valeurs complexes"""
#     if isinstance(value, (str, int, float, bool)):
#         return value

#     if isinstance(value, Decimal):
#         return float(value)

#     if isinstance(value, (datetime, date, time)):
#         return value.isoformat()

#     if isinstance(value, UUID):
#         return str(value)

#     if value is None:
#         return None

#     if isinstance(value, FieldFile):
#         return value.name if value else None

#     if isinstance(value, Model):
#         return value.pk

#     if isinstance(value, QuerySet):
#         return list(value.values_list("pk", flat=True))

#     return str(value)


# def serialize_data(data):
#     """Sérialise un dictionnaire complet"""
#     if not isinstance(data, dict):
#         return data
#     return {key: serialize_value(val) for key, val in data.items()}


# # ----------------------------------------
# # 🔥 RÉCUPÉRATION AUTOMATIQUE DU NOM DE FICHIER LIÉ
# # ----------------------------------------

# def get_document_filename(instance):
#     """
#     Retourne le nom du ou des fichiers associés selon le modèle.
#     """
#     # ---- Document ----
#     if isinstance(instance, Document):
#         return instance.nom_fichier

#     # ---- Transcription ----
#     if isinstance(instance, Transcription):
#         if instance.document:
#             return instance.document.nom_fichier

#     # ---- Anomalie (ManyToMany vers Document) ----
#     if isinstance(instance, Anomalie):
#         docs = instance.document.all()
#         if docs.exists():
#             return ", ".join([d.nom_fichier for d in docs])

#     # ---- Correction (via anomalie -> document) ----
#     if isinstance(instance, Correction):
#         anomaly = instance.anomalie
#         if anomaly:
#             docs = anomaly.document.all()
#             if docs.exists():
#                 return ", ".join([d.nom_fichier for d in docs])

#     return None


# # ----------------------------------------
# # 🔥 CRÉATION DU LOG
# # ----------------------------------------

# def create_audit_log(instance, action, old_data=None, new_data=None):
#     old_data = serialize_data(old_data)
#     new_data = serialize_data(new_data)

#     user = get_current_user()
#     request = get_current_request()
#     ip = get_client_ip(request)

#     if not user or user.is_anonymous:
#         return  # ne log jamais sans utilisateur

#     # 🔥 Ajout automatique du nom du fichier lié
#     filename = get_document_filename(instance)

#     AuditLog.objects.create(
#         utilisateur=user,
#         action=action,
#         modele=instance.__class__.__name__,
#         objet_id=instance.pk,
#         document_filename=filename,
#         ancienne_valeur=old_data,
#         nouvelle_valeur=new_data,
#         adresse_ip=ip,
#     )


# # ----------------------------------------
# # 🔁 LOG DES MODIFICATIONS
# # ----------------------------------------

# def get_object_data(instance):
#     """Retourne un dict complet représentant l'objet"""
#     try:
#         return model_to_dict(instance)
#     except Exception:
#         return {}


# @receiver(post_save)
# def log_save(sender, instance, created, **kwargs):
#     # Ignore les modèles AuditLog
#     if sender is AuditLog:
#         return

#     new_data = get_object_data(instance)

#     if created:
#         create_audit_log(instance, "CREATION", old_data=None, new_data=new_data)
#     else:
#         try:
#             old_instance = sender.objects.get(pk=instance.pk)
#             old_data = get_object_data(old_instance)
#         except sender.DoesNotExist:
#             old_data = None

#         create_audit_log(instance, "MISE À JOUR", old_data=old_data, new_data=new_data)


# @receiver(post_delete)
# def log_delete(sender, instance, **kwargs):
#     if sender is AuditLog:
#         return

#     old_data = get_object_data(instance)

#     create_audit_log(instance, "SUPPRESSION", old_data=old_data, new_data=None)

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed
)
from django.conf import settings

from audit.models import AuditLog
from audit.middleware import get_current_user, get_current_request

from datetime import datetime, date, time
from decimal import Decimal
from django.db.models import Model, QuerySet
from django.db.models.fields.files import FieldFile
from uuid import UUID
import logging

# 🔥 Import des modèles métiers
from data.models import Document, Transcription, Anomalie, Correction

logger = logging.getLogger(__name__)

# ----------------------------------------
# 🔧 UTILITAIRES
# ----------------------------------------

def get_client_ip(request):
    if request is None:
        return None

    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]

    return request.META.get("REMOTE_ADDR")


def serialize_value(value):
    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (datetime, date, time)):
        return value.isoformat()

    if isinstance(value, UUID):
        return str(value)

    if value is None:
        return None

    if isinstance(value, FieldFile):
        return value.name if value else None

    if isinstance(value, Model):
        return value.pk

    if isinstance(value, QuerySet):
        return list(value.values_list("pk", flat=True))

    return str(value)


def serialize_data(data):
    if not isinstance(data, dict):
        return data
    return {key: serialize_value(val) for key, val in data.items()}


# ----------------------------------------
# 📄 RÉCUPÉRATION DU NOM DE FICHIER LIÉ
# ----------------------------------------

def get_document_filename(instance):
    if isinstance(instance, Document):
        return instance.nom_fichier

    if isinstance(instance, Transcription) and instance.document:
        return instance.document.nom_fichier

    if isinstance(instance, Anomalie):
        docs = instance.document.all()
        if docs.exists():
            return ", ".join(d.nom_fichier for d in docs)

    if isinstance(instance, Correction):
        anomaly = instance.anomalie
        if anomaly:
            docs = anomaly.document.all()
            if docs.exists():
                return ", ".join(d.nom_fichier for d in docs)

    return None


# ----------------------------------------
# 🔥 CRÉATION DU LOG
# ----------------------------------------

def create_audit_log(instance, action, old_data=None, new_data=None):
    user = get_current_user()
    request = get_current_request()
    ip = get_client_ip(request)

    if not user or user.is_anonymous:
        return

    AuditLog.objects.create(
        utilisateur=user,
        action=action,
        modele=instance.__class__.__name__ if instance else "User",
        objet_id=str(instance.pk) if instance else None,
        document_filename=get_document_filename(instance) if instance else None,
        ancienne_valeur=serialize_data(old_data),
        nouvelle_valeur=serialize_data(new_data),
        adresse_ip=ip,
    )


# ----------------------------------------
# 🔁 LOG DES MODIFICATIONS (CORRIGÉ)
# ----------------------------------------

def get_object_data(instance):
    try:
        return model_to_dict(instance)
    except Exception:
        return {}


@receiver(pre_save)
def capture_old_data(sender, instance, **kwargs):
    """
    Capture l'ancien état AVANT sauvegarde (corrige le bug post_save)
    """
    if sender is AuditLog:
        return

    if instance.pk:
        try:
            instance._old_data = get_object_data(sender.objects.get(pk=instance.pk))
        except sender.DoesNotExist:
            instance._old_data = None


@receiver(post_save)
def log_save(sender, instance, created, **kwargs):
    if sender is AuditLog:
        return

    new_data = get_object_data(instance)

    if created:
        create_audit_log(instance, "CREATION", None, new_data)
    else:
        old_data = getattr(instance, "_old_data", None)
        create_audit_log(instance, "MISE À JOUR", old_data, new_data)


@receiver(post_delete)
def log_delete(sender, instance, **kwargs):
    if sender is AuditLog:
        return

    old_data = get_object_data(instance)
    create_audit_log(instance, "SUPPRESSION", old_data, None)


# ----------------------------------------
# 🔐 AUTHENTIFICATION (CE QUI TE MANQUAIT)
# ----------------------------------------

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    AuditLog.objects.create(
        utilisateur=user,
        action="LOGIN",
        modele="User",
        objet_id=str(user.id),
        adresse_ip=get_client_ip(request),
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    AuditLog.objects.create(
        utilisateur=user,
        action="LOGOUT",
        modele="User",
        objet_id=str(user.id),
        adresse_ip=get_client_ip(request),
    )


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    AuditLog.objects.create(
        utilisateur=None,
        action="LOGIN_FAILED",
        modele="User",
        objet_id=credentials.get("username"),
        adresse_ip=get_client_ip(request),
    )

