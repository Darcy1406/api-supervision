from django.shortcuts import render
from django.core import serializers
from django.http import HttpResponse
from .models import Fichiers
# Create your views here.
def index(request):
    fichiers = Fichiers.objects.all()
    f = open("test.pdf", 'wb')
    f.write(fichiers[0].contenu)
    f.close()
    # json = serializers.serialize("json", fichiers)
    return HttpResponse(fichiers[0].contenu)
