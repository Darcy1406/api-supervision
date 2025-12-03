from rest_framework import serializers
from audit.models import AuditLog
from django.utils.timezone import localtime

class AuditLogSerializer(serializers.ModelSerializer):
    # Champ personnalisé pour afficher prénom + nom
    utilisateur = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "utilisateur",
            "action",
            "modele",
            "objet_id",
            "document_filename",   # ✅ ajout pour afficher le nom du fichier lié
            "ancienne_valeur",
            "nouvelle_valeur",
            "date_action",
            "adresse_ip",
        ]

    def get_utilisateur(self, obj):
        """
        Retourne 'Nom Prénom' depuis la relation Authentification.utilisateur
        """
        try:
            auth_user = obj.utilisateur
            if not auth_user:
                return "—"

            profile = getattr(auth_user, "utilisateur", None)
            if not profile:
                return "—"

            prenom = profile.prenom or ""
            nom = profile.nom or ""
            full_name = f"{nom} {prenom}".strip()

            return full_name if full_name else "—"

        except Exception:
            return "—"
        
    def get_date_action(self, obj):
        # Conversion automatique en heure locale Madagascar
        # return localtime(obj.date_action).strftime("%Y-%m-%d %H:%M:%S")
        return localtime(obj.date_action).isoformat()


