from django.contrib.auth import authenticate, login, logout
from django.middleware import csrf
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.core import serializers
from .models import Utilisateur, Authentification, Poste_comptable, Zone
from data.models import Piece 
import json, requests
from django.core.mail import send_mail


class GetCSRFToken(APIView):
    permission_classes = []
    authentication_classes = []
    def get(self, request):
        # renvoie le cookie csrf (set-cookie) et en même temps on peut envoyer le token
        token = csrf.get_token(request)
        return Response({"csrfToken": token})


# Login
class LoginView(APIView):
    permission_classes = []
    authentication_classes = []
    def post(self, request):

        # token = request.data.get("captchaToken")
        # secret_key = "6LeVF8srAAAAAEQBQ-2NnWOrU_rCgGp7RrESw7FF"
        # url = "https://www.google.com/recaptcha/api/siteverify"
        # data = {"secret": secret_key, "response": token}

        # r = requests.post(url, data=data)
        # result = r.json()

        # if result.get("success"):

        identifiant = request.data.get("identifiant")
        password = request.data.get("password")

        user = authenticate(request, username=identifiant, password=password)

        if user is not None:
            login(request, user)

            texte = {"detail": "Connecté", "identifiant": user.identifiant}
            return Response(texte)
        
        return JsonResponse({"error": "Incorrecte: Veuillez verifier vos identifiants et ressayer"})
        # else:
        #     return JsonResponse({"error": "Veuillez valider le reCAPTCHA"})


# Logout (Deconnexion)
class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return JsonResponse({"detail": "Logged out"})

# UserView
class UserView(APIView):

    # Requete GET
    def get(self, request):
        print(f'request.user {request.user.is_authenticated}')
        if request.user.is_authenticated:

            auth = Authentification.objects.filter(identifiant=request.user.identifiant, password=request.user.password).values(
                'id',
                'utilisateur_id',
                'utilisateur__nom',
                'utilisateur__prenom',
                'utilisateur__fonction',
                'utilisateur__zone__nom_zone',
                'utilisateur__zone__id',
                'identifiant',
            )
             
            # user = {"id": auth.utilisateur.pk , "nom": auth.utilisateur.nom, "prenom": auth.utilisateur.prenom, "fonction": auth.utilisateur.fonction}
            return JsonResponse(list(auth), safe=False)
        return Response({"user": None}, status=status.HTTP_401_UNAUTHORIZED)
    

    # Requete POST
    def post(self, request):

        # Script : ajouter un utilisateur
        if request.data.get('action') == 'ajouter_utilisateur':
            
            if request.data.get('fonction').upper() != "Directeur".upper():
                user = Utilisateur(
                    nom = request.data.get('nom'),
                    prenom = request.data.get('prenom'),
                    email = request.data.get('email'),
                    fonction = request.data.get('fonction'),
                    zone_id = request.data.get('zone')
                )
            else:
                user = Utilisateur(
                    nom = request.data.get('nom'),
                    prenom = request.data.get('prenom'),
                    email = request.data.get('email'),
                    fonction = request.data.get('fonction'),
                )
            user.save()

            return JsonResponse({'user_id': user.id})

        # Script : creer l'authentification de l'utiliseur et lui envoyer un email
        if request.data.get("action") == "creer_authentification_utilisateur":
            email = request.data.get("email")
            identifiant = request.data.get("identifiant")
            password = request.data.get("password")
            id_user = request.data.get('id_user')
            user = Utilisateur.objects.get(id=id_user)
            
            if user.fonction.upper() == 'auditeur'.upper(): 
                # Message à envoyer
                sujet = "Vos identifiants d'accès"
                message = f"""
                                Bonjour,

                                Votre compte a été créé avec succès.

                                Voici vos informations de connexion :

                                Identifiant : {identifiant}
                                Mot de passe : {password}

                                Vous pouvez maintenant vous connecter à la plateforme.

                                Cordialement,
                                L'équipe technique.
                            """

                try:
                    
                    send_mail(
                        sujet,
                        message,
                        None,             # utilise DEFAULT_FROM_EMAIL
                        [email],
                        fail_silently=False,
                    )

                    Authentification.objects.create_user(
                    identifiant=identifiant,
                    password=password,
                    utilisateur=user
                    )
                    return JsonResponse({"succes": "L'utilisateur peut maintenant acceder au système"})
                
                except Exception as e:
                    return Response({"error": str(e)})
            else:
                # Message à envoyer
                sujet = "Vos identifiants d'accès"
                message = f"""
                                Bonjour,

                                Votre compte a été créé avec succès.

                                Voici vos informations de connexion :

                                Identifiant : {identifiant}
                                Mot de passe : {password}

                                Vous pouvez maintenant vous connecter à la plateforme.

                                Cordialement,
                                L'équipe technique.
                            """

                try:
                    
                    send_mail(
                        sujet,
                        message,
                        None,             # utilise DEFAULT_FROM_EMAIL
                        [email],
                        fail_silently=False,
                    )

                    Authentification.objects.create_superuser(
                    identifiant=identifiant,
                    password=password,
                    utilisateur=user
                    )

                    return JsonResponse({"succes": "L'utilisateur peut maintenant acceder au système"})
                
                except Exception as e:
                    return Response({"error": str(e)})
                

        # Script : lister tous les utilisateurs (dans l'interface admin)
        if request.data.get('action') == 'lister_tous_les_utilisateurs':
            users = Utilisateur.objects.all().values(
                'id',
                'nom',
                'prenom',
                'email',
                'fonction',
                'zone__nom_zone',
                'zone_id',
                'authentification',
            )
            return JsonResponse(list(users), safe=False)

        if request.data.get('action') == 'obtenir_nombre_total_utilisateurs':
            nb_count = Utilisateur.objects.count()
            return JsonResponse({'total_utilisateur': nb_count})

        if request.data.get('action') == 'recuperer_auditeurs_zone':
            auditeurs = Utilisateur.objects.filter(fonction__icontains='auditeur', zone__id=request.data.get('zone')).values('id', 'nom', 'prenom', 'zone_id')
            return JsonResponse(list(auditeurs), safe=False)
        
        elif request.data.get('action') == 'recuperer_auditeurs':
            auditeurs = Utilisateur.objects.filter(fonction__icontains='auditeur').values('id', 'nom', 'prenom', 'zone_id', 'zone__nom_zone')
            return JsonResponse(list(auditeurs), safe=False)
    

    # Requete PUT
    def put(self, request):
        user = Utilisateur.objects.get(id=request.data.get('id'))

        user.nom = request.data.get('nom')
        user.prenom = request.data.get('prenom')
        user.email = request.data.get('email')
        user.fonction = request.data.get('fonction')
        user.zone_id = request.data.get('zone')

        user.save()

        return JsonResponse({'succes': 'Utilisateur modifié avec succès'})


    # Requete DELETE
    def delete(self, request):
        id = request.data.get('id')
        if not id:
            return JsonResponse({"error": "ID manquant"}, status=400)
        
        try:
            user = Utilisateur.objects.get(id=id)
            user.delete()
            return JsonResponse({"succes": "Utilisateur supprimé avec succès"})
        except Poste_comptable.DoesNotExist:
            return JsonResponse({"error": "Utilisateur non trouvé"}, status=404)


# Zone
class ZoneView(APIView):
    def get(self, request):
        zones = Zone.objects.all().values('id', 'nom_zone')
        return JsonResponse(list(zones), safe=False)


# PosteComptable
class PosteComptableView(APIView):

    def post(self, request):

        # Ce script va ajouter un poste_comptable vers la BD
        if request.data.get('action') == 'ajouter_poste_comptable':
            poste_comptable = Poste_comptable(
                code_poste=request.data.get('code_poste'), 
                nom_poste=request.data.get('nom_poste'), 
                lieu=request.data.get('lieu'), 
                poste=request.data.get('poste'), 
                responsable=request.data.get('responsable'), 
                utilisateur_id=request.data.get('auditeur'), 
            )
            poste_comptable.save()
            return JsonResponse({'succes': 'Poste comptable ajoutée avec succès'})

        if request.data.get('action') == 'afficher_les_postes_comptables':
            poste = Poste_comptable.objects.filter(utilisateur_id=request.data.get('user_id')).values("nom_poste", 'utilisateur_id', 'utilisateur__zone_id')
            return JsonResponse(list(poste), safe=False)
        
        if request.data.get('action') == 'afficher_tous_les_postes_comptables':
            poste = Poste_comptable.objects.all().values("nom_poste", 'utilisateur_id', 'utilisateur__zone_id')
            return JsonResponse(list(poste), safe=False)    
        
        elif request.data.get('action') == 'afficher_les_postes_comptables_zone':
            poste = Poste_comptable.objects.filter(utilisateur__zone__id=request.data.get('zone')).values('nom_poste', 'utilisateur_id','utilisateur__zone_id')
            return JsonResponse(list(poste), safe=False)
        
        elif request.data.get('action') == 'afficher_les_postes_comptables_specifique_a_une_piece':
            piece_data = request.data.get("piece")

            # Si c’est une chaîne, on la transforme en liste d’un seul élément
            if isinstance(piece_data, str):
                piece_data = [piece_data]

            # Si c’est None, on met une liste vide pour éviter les erreurs
            piece_data = piece_data or []

            # On récupère les objets Piece correspondants
            pieces = Piece.objects.filter(nom_piece__in=piece_data)

            poste = Poste_comptable.objects.filter(utilisateur_id=request.data.get('utilisateur_id'), pieces__in=pieces).distinct().values("id", "nom_poste")
            return JsonResponse(list(poste), safe=False)
        
        elif request.data.get('action') == 'obtenir_nombre_total_poste_comptables':
            nb_count = Poste_comptable.objects.count()
            return JsonResponse({'total_poste_comptables': nb_count})

        elif request.data.get('action') == 'recuperer_les_infos_des_postes_comptables':
            poste = Poste_comptable.objects.all().values(
                'id',
                'code_poste',
                'nom_poste',
                'lieu',
                'responsable',
                'poste',
                'utilisateur_id',
            ).order_by('-id')
            # poste_json = serializers.serialize('json', poste)
            # print('ato')
            return JsonResponse(list(poste), safe=False)

        elif request.data.get('action') == 'selectionner_poste_piece':
            poste = Poste_comptable.objects.select_related('pieces').filter(pieces__nom_piece=request.data.get('piece')).values_list('poste', flat=True).distinct()
            return JsonResponse(list(poste), safe=False)
            

    def get(self, request):
        poste = Poste_comptable.objects.all().values('poste').distinct().order_by('poste')
        return JsonResponse(list(poste), safe=False)
    

    def put(self, request):

        if request.data.get('action') == 'modifier_poste_comptable':

            poste_comptable = Poste_comptable.objects.get(id=request.data.get('id'))

            poste_comptable.code_poste = request.data.get('code_poste')
            poste_comptable.nom_poste = request.data.get('nom_poste')
            poste_comptable.lieu = request.data.get('lieu')
            poste_comptable.poste = request.data.get('poste')
            poste_comptable.responsable = request.data.get('responsable')
            poste_comptable.utilisateur_id = request.data.get('auditeur')

            poste_comptable.save()

            return JsonResponse({'succes': 'Poste comptable modifié avec succès'})


    def delete(self, request):

        # Récupération de l'id depuis les données POST
        id = request.data.get('id')
        if not id:
            return JsonResponse({"error": "ID manquant"}, status=400)
        
        try:
            poste = Poste_comptable.objects.get(id=id)
            poste.delete()
            return JsonResponse({"succes": "Poste comptable supprimé avec succès"})
        except Poste_comptable.DoesNotExist:
            return JsonResponse({"error": "Poste non trouvé"}, status=404)

            
    