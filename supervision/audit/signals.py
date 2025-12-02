from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict
from audit.models import AuditLog
from audit.middleware import get_current_user, get_current_request
from datetime import datetime, date, time
from decimal import Decimal
from django.forms.models import model_to_dict
from django.db.models import Model, QuerySet
from django.db.models.fields.files import FieldFile
# utils_audit.py (ou dans signals.py où tu veux)
from django.utils.timezone import is_aware
from uuid import UUID
import logging
logger = logging.getLogger(__name__)

def make_json_safe(value):
    """Convertit une valeur en quelque chose de JSON-serializable."""
    # model instance -> renvoyer pk si disponible sinon str()
    if isinstance(value, Model):
        try:
            return value.pk
        except Exception:
            return str(value)

    # QuerySet ou manager de relation -> liste de pks
    if isinstance(value, QuerySet):
        return [getattr(o, 'pk', str(o)) for o in value]

    # FieldFile (FileField) -> nom du fichier (ou url si tu préfères)
    if isinstance(value, FieldFile):
        return value.name

    # Datetime / date / time
    if isinstance(value, (datetime, date, time)):
        # datetime aware -> isoformat
        try:
            return value.isoformat()
        except Exception:
            return str(value)

    # Decimal -> str (ou float si tu veux)
    if isinstance(value, Decimal):
        return str(value)

    # UUID
    if isinstance(value, UUID):
        return str(value)

    # Dict -> récursif
    if isinstance(value, dict):
        return {k: make_json_safe(v) for k, v in value.items()}

    # List / tuple / set -> récursif
    if isinstance(value, (list, tuple, set)):
        return [make_json_safe(v) for v in value]

    # Fallback : types simples (int, str, bool, None) ou str()
    try:
        # Certains objets ont __iter__ / mauvais comportement -> on garde safe
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)
    except Exception:
        return str(value)



def safe_model_to_dict(instance):
    """Retourne un dict serializable JSON représentant l'instance."""
    # On commence par model_to_dict pour récupérer les champs simples et m2m (pk list)
    try:
        data = model_to_dict(instance)
    except Exception:
        # fallback: construire à partir des fields
        data = {}
        for field in instance._meta.concrete_fields + instance._meta.many_to_many:
            try:
                val = getattr(instance, field.name)
                data[field.name] = val
            except Exception:
                data[field.name] = None

    # Convertir récursivement
    safe = {}
    for k, v in data.items():
        safe[k] = make_json_safe(v)
    return safe



def serialize_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def serialize_data(data):
    if not data:
        return data
    return {key: serialize_value(value) for key, value in data.items()}


def get_client_ip(request):
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def create_audit_log(instance, action, old_data=None, new_data=None):
    old_data = serialize_data(old_data)
    new_data = serialize_data(new_data)

    user = get_current_user()
    request = get_current_request()
    ip = get_client_ip(request)
    if not user or user.is_anonymous:
        return
    AuditLog.objects.create(
        utilisateur=user,
        action=action,
        modele=instance.__class__.__name__,
        objet_id=instance.pk,
        ancienne_valeur=old_data,
        nouvelle_valeur=new_data,
        adresse_ip=ip  # ✅ maintenant on l’enregistre proprement
    )

# @receiver(post_save)
# def log_save(sender, instance, created, **kwargs):
    # if sender.__name__ == 'AuditLog':
    #     return
    
    # action = "Création" if created else "Modification"

    # new_data = safe_model_to_dict(instance)

    # create_audit_log(instance, action, None, new_data)


@receiver(post_save)
def log_save(sender, instance, created, **kwargs):
    # éviter la boucle si on journalise AuditLog lui-même
    if sender.__name__ == 'AuditLog':
        return

    action = "Création" if created else "Modification"
    try:
        new_data = safe_model_to_dict(instance)
    except Exception as e:
        # journaliser et continuer avec une version minimale
        logger.exception("safe_model_to_dict a échoué pour %s (id=%s): %s", sender.__name__, getattr(instance, 'pk', None), e)
        new_data = {"id": getattr(instance, "pk", None), "model": sender.__name__}

    # Si tu veux enregistrer old_data, gère de la même façon
    try:
        create_audit_log(instance, action, None, new_data)
    except TypeError as te:
        # journaliser le contenu incriminé pour debug
        logger.exception("create_audit_log a provoqué TypeError — new_data: %s", new_data)
        # Optionnel : convertir new_data en chaîne json-safe puis la stocker
        create_audit_log(instance, action, None, {"raw": str(new_data)})
    except Exception:
        logger.exception("Erreur inconnue lors de la création de l'audit log pour %s id=%s", sender.__name__, getattr(instance, 'pk', None))


@receiver(post_delete)
def log_delete(sender, instance, **kwargs):
    if sender.__name__ == 'AuditLog':
        return
    old_data = model_to_dict(instance)
    create_audit_log(instance, "Suppression", old_data, None)
