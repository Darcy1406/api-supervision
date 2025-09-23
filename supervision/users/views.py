import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.core import serializers
from django.http import JsonResponse
from rest_framework.decorators import api_view
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Authentification


# Create your views here.
@ensure_csrf_cookie
def get_csrf(request):
    return JsonResponse({"csrfToken": request.COOKIES.get("csrftoken")})


@api_view(["POST"])
def authentification(request):
        
        # token = request.data.get("token")

        # secret_key = "6LeVF8srAAAAAEQBQ-2NnWOrU_rCgGp7RrESw7FF"
        # url = "https://www.google.com/recaptcha/api/siteverify"
        # data = {"secret": secret_key, "response": token}

        # r = requests.post(url, data=data)
        # result = r.json()

        # if result.get("success"):
            # authentification = Authentification.objects.all()
            # print(serializers.serialize('json', authentification))
    is_existe = Authentification.objects.filter(identifiant=request.data.get('identifiant'), password=request.data.get('password'))

            
            
    if(is_existe):
        texte = {'message': 'Correcte'}
    else:
        texte = {'message': 'Incorrecte'}
            
              
        # else:
        #     texte = {'message': 'Authentification non valide'}
            
        
        # json_texte = serializers.serialize('json', texte)
    return JsonResponse(texte)