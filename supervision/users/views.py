# import requests, json
# from django.shortcuts import render
# from django.http import JsonResponse
# from django.core import serializers
# from django.http import JsonResponse, HttpResponse
# from rest_framework.decorators import api_view
# from django.views.decorators.csrf import ensure_csrf_cookie
# from .models import Authentification


# # Create your views here.
# # @ensure_csrf_cookie
# def get_csrf(request):
#     return JsonResponse({"csrfToken": request.COOKIES.get("csrftoken")})


# @api_view(["POST"])
# def login(request):
        
#         # token = request.data.get("token")

#         # secret_key = "6LeVF8srAAAAAEQBQ-2NnWOrU_rCgGp7RrESw7FF"
#         # url = "https://www.google.com/recaptcha/api/siteverify"
#         # data = {"secret": secret_key, "response": token}

#         # r = requests.post(url, data=data)
#         # result = r.json()

#         # if result.get("success"):
#             # authentification = Authentification.objects.all()
#             # print(serializers.serialize('json', authentification))
#     is_existe = Authentification.objects.filter(identifiant=request.data.get('identifiant'), password=request.data.get('password'))

            
            
#     if(is_existe):
#         # print(is_existe)
#         user = serializers.serialize("json", is_existe)
#         # user = json.dumps(is_existe)
#         # print(user)
#         # texte = {'message': "Correcte"}
#         return JsonResponse(user)
#     else:
#         texte = {'message': 'Incorrecte'}
#         return JsonResponse(texte)

            
              
#         # else:
#         #     texte = {'message': 'Authentification non valide'}
            
        
#         # json_texte = serializers.serialize('json', texte)

# def user():
#     print("Bonjour")

from django.contrib.auth import authenticate, login, logout
from django.middleware import csrf
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.core import serializers
from .models import Utilisateur, Authentification, Poste_comptable
from data.models import Piece 
import json


class GetCSRFToken(APIView):
    permission_classes = []
    authentication_classes = []
    def get(self, request):
        # renvoie le cookie csrf (set-cookie) et en même temps on peut envoyer le token
        token = csrf.get_token(request)
        return Response({"csrfToken": token})


class LoginView(APIView):
    permission_classes = []
    authentication_classes = []
    def post(self, request):
        username = request.data.get("identifiant")
        password = request.data.get("password")

        user = authenticate(request, identifiant=username, password=password)

        if user is not None:
            login(request, user)
            # sessionid cookie sera géré automatiquement par Django
            texte = {"detail": "Connecté", "message": user.identifiant}
            return Response(texte)
            # return JsonResponse({"detail": "Logged in", "username": user.identifiant})
        return JsonResponse({"error": "Incorrecte: Veuillez verifier vos identifiants et ressayer"})


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return JsonResponse({"detail": "Logged out"})


class UserView(APIView):
    def get(self, request):
        if request.user.is_authenticated:

            auth = Authentification.objects.get(identifiant=request.user.identifiant, password=request.user.password)
             
            user = {"id": auth.utilisateur.pk , "nom": auth.utilisateur.nom, "prenom": auth.utilisateur.prenom, "fonction": auth.utilisateur.fonction}
            return JsonResponse(user)
        return Response({"user": None}, status=status.HTTP_401_UNAUTHORIZED)


class PosteComptableView(APIView):
    def post(self, request):

        if request.data.get('action') == 'afficher_tous_les_postes_comptables':
            poste = Poste_comptable.objects.filter(utilisateur_id=request.data.get('user_id')).values("nom_poste")
            return JsonResponse(list(poste), safe=False)
        
        elif request.data.get('action') == 'afficher_les_postes_comptables_specifique_a_une_piece':
            poste = Poste_comptable.objects.filter(utilisateur_id=request.data.get('utilisateur_id'), pieces=Piece.objects.get(nom_piece=request.data.get("piece"))).distinct().values("id", "nom_poste")
            return JsonResponse(list(poste), safe=False)
            
    