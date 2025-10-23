from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.core import serializers
from rest_framework.decorators import api_view
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Agenda
from datetime import date, time
from rest_framework.decorators import api_view
import json

# Create your views here.
@ensure_csrf_cookie
def get_csrf(request):
    return JsonResponse({"csrfToken": request.COOKIES.get("csrftoken")})


def index(request):
    liste_agenda = Agenda.objects.all()
    liste_agenda_json = serializers.serialize('json', liste_agenda)
    return HttpResponse(liste_agenda_json)

@api_view(["POST"])
def create(request):
    agenda = Agenda(
        description = request.data.get('description'),
        date_evenement = request.data.get('date_agenda'),
        heure_evenement = request.data.get('heure_agenda'),
        utilisateur_id = request.data.get('utilisateur_id'),
    )

    agenda.save()
    
    message = { 'message': 'Ajout effectuee avec succes' }
    return JsonResponse(message)


@api_view(["POST"])
def read(request):
    evenements = Agenda.objects.filter(utilisateur_id=request.data.get("utilisateur_id"))
    # print(serializers.serialize("json", evenements))
    return JsonResponse(json.loads(serializers.serialize("json", evenements)), safe=False)


