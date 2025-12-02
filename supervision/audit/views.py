from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from audit.models import AuditLog
from audit.serializers import AuditLogSerializer
from rest_framework.views import APIView
from rest_framework.response import Response

# Create your views here.


class AuditLogView(APIView):
    def get(self, request):
        # Récupérer tous les logs, les plus récents en premier
        audit_logs = AuditLog.objects.all().order_by('-date_action')
        
        # Sérialiser les données
        serializer = AuditLogSerializer(audit_logs, many=True)
        
        # Retourner la réponse JSON
        return Response(serializer.data)


# class AuditLogView(APIView):
#     queryset = AuditLog.objects.all().order_by('-date_action')
#     serializer_class = AuditLogSerializer
#     permission_classes = [IsAuthenticated]  # tu peux retirer ça pour les tests
