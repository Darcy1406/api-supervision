from rest_framework import serializers
from audit.models import AuditLog

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
            "ancienne_valeur",
            "nouvelle_valeur",
            "date_action",
            "adresse_ip",
        ]

    def get_utilisateur(self, obj):
        """
        Retourne le prénom et le nom de l'utilisateur lié à Authentification
        """
        if obj.utilisateur and obj.utilisateur.utilisateur:
            prenom = obj.utilisateur.utilisateur.prenom or ""
            nom = obj.utilisateur.utilisateur.nom or ""
            return f"{nom} {prenom}".strip()
        return "—"

