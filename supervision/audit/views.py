from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from audit.models import AuditLog
from audit.serializers import AuditLogSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse
from datetime import datetime

# Create your views here.


class AuditLogView(APIView):

    def post(self, request):
        nb_users_login = []
        all_month = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        for month in all_month:
            nb_count = AuditLog.objects.filter(date_action__month=month, action__icontains='login', date_action__year=datetime.now().year).count()
            nb_users_login.append(nb_count)

        return JsonResponse(list(nb_users_login), safe=False)


    def get(self, request):
        # Récupérer tous les logs, les plus récents en premier
        audit_logs = AuditLog.objects.all().order_by('-date_action')
        
        # Sérialiser les données
        serializer = AuditLogSerializer(audit_logs, many=True)
        
        # Retourner la réponse JSON
        return Response(serializer.data)
