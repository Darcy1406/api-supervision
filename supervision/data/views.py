from django.shortcuts import render
from django.core import serializers
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from .models import Piece, Document, Transcription, Compte, PieceCompte, Anomalie, Total_montant_transcription_filtrees, Correction, Proprietaire, Exercice
from rest_framework.decorators import api_view
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import F
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from users.models import Poste_comptable
from datetime import datetime
import json
import os.path
import shutil
import pandas as pd
import calendar
from datetime import date
from rest_framework.permissions import IsAuthenticated
from django.db.models import Max
from fpdf import FPDF
from django.http import HttpResponse


# Create your views here.

# Proprietaire
class ProprietaireView(APIView):
    
    # Requete GET : Va afficher toutes les proprietaires de comptes
    def get(self, request):
        proprio = Proprietaire.objects.all().values('id', 'nom_proprietaire')
        return JsonResponse(list(proprio), safe=False)


# Piece
class PieceView(APIView):

    # Requete POST
    def post(self, request):

        # Ce script sert a ajouter une piece
        if request.data.get('action') == 'ajouter_piece':
        
            poste_comptable = request.data.get('poste_comptable')

            piece_object = Piece(
                nom_piece = request.data.get("nom_piece"),
                periode = request.data.get("periode"),
            )

            piece_object.save()

            for poste in poste_comptable:
                poste_comptable_filter = Poste_comptable.objects.filter(poste=poste)
                piece_object.poste_comptable.add(*poste_comptable_filter)

            return JsonResponse({"succes": "La pièce a été ajoutée avec succès"})
        
        # Cette script sert a recuperer la periode d'une piece
        elif request.data.get('action') == 'recuperer_periode_piece':
            periode = Piece.objects.filter(nom_piece=request.data.get('piece')).values_list('periode')
            return JsonResponse(list(periode), safe=False)

        elif request.data.get('action') == 'obtenir_nombre_total_pieces':
            nb_count = Piece.objects.count()
            return JsonResponse({'total_pieces': nb_count})

    # Requete PUT (Modifier une piece)
    def put(self, request):

        poste_comptable = request.data.get('poste_comptable')

        piece = Piece.objects.get(pk=request.data.get("id"))
        piece.nom_piece = request.data.get("nom_piece")
        piece.periode = request.data.get("periode")

        piece.save()

        piece.poste_comptable.clear()
        
        for poste in poste_comptable:
            poste_comptable_filter = Poste_comptable.objects.filter(poste=poste)
            piece.poste_comptable.add(*poste_comptable_filter)

        return JsonResponse({"succes": "La pièce a été modifiée avec succès"})


    # Requete DELETE (Supprimer une piece)
    def delete(self, request):
        id = request.data.get('id')
        if not id: 
            return JsonResponse({"error": "ID manquant"}, status=400)
        
        try:
            piece = Piece.objects.get(id=id)
            piece.delete()
            return JsonResponse({'succes': 'La pièce a été supprimée avec succes'})
        except Piece.DoesNotExist:
            return JsonResponse({"error": "Pièce non trouvée"}, status=404)


    # Requete GET (Obtenir le nom de toutes les pieces)
    def get(self, request):
        pieces = Piece.objects.all().order_by('nom_piece')
        pieces_serialize = serializers.serialize('json', pieces)
        return JsonResponse(json.loads(pieces_serialize), safe=False)
    

# Exercice
class ExerciceView(APIView):

    # Requete POST (Ajouter un exercice)
    def post(self, request):
        exercice = Exercice(
            annee=request.data.get('annee')
        )
        exercice.save()
        return JsonResponse({'succes': 'Nouveau exercice ajouté avec succès'})

    # Requete GET (Lister tous les exercices par ordre decroissant de l'id)
    def get(self, request):
        exercices = Exercice.objects.all().values('id', 'annee').order_by('-id')
        return JsonResponse(list(exercices), safe=False)


# Liaison piece - compte
class PieceCompteView(APIView):

    # Requete POST
    def post(self, request):

        # Ajouter une liaison entre une piece et un compte
        if request.data.get("action") == 'ajouter':
            nature = request.data.get('nature')

            piece_et_compte = PieceCompte(
                piece_id = request.data.get('piece'),
                compte = Compte.objects.get(numero=request.data.get('compte')),
                nature = ", ".join(nature)
            )

            piece_et_compte.save()

            return JsonResponse({'succes': 'La liaison entre le compte et la pièce a ete établie avec succès'})
        
        # Filtrer les liaisons par type de piece
        elif request.data.get("action") == "filtrer_liaison":
           
            piece_et_compte = PieceCompte.objects.filter(piece=Piece.objects.get(nom_piece=request.data.get('piece'))).select_related('compte').distinct().values('compte__numero', 'nature')

            return JsonResponse(list(piece_et_compte), safe=False)
    

    # Requete PUT (modifier une liaison entre une piece et un compte)
    def put(self, request):
        nature = request.data.get('nature')

        piece_compte = PieceCompte.objects.get(pk=request.data.get('id'))

        piece_compte.piece_id = request.data.get('piece')
        piece_compte.compte = Compte.objects.get(numero=request.data.get('compte'))
        piece_compte.nature = ', '.join(nature)

        piece_compte.save()

        return JsonResponse({'succes': 'Modification éffectuée avec succès'})

    # Requete GET (Lister toutes les liaisons entre les pieces et les comptes)
    def get(self, request):
        piece_compte = PieceCompte.objects.select_related('compte', 'piece').values(
            'id',
            'compte__numero',
            'piece_id',
            'piece__nom_piece',
            'nature',
            'created_at',
            'updated_at',
        ).order_by('piece__nom_piece')
        return JsonResponse(list(piece_compte), safe=False)


# Document
class DocumentView(APIView):

    # Requete POST
    def post(self, request):

        # Ce script sert ajouter un document
        if request.data.get("action") == 'ajouter_un_document':
            contenu = request.FILES.get("fichier")
            poste_comptable_nom = request.data.get("poste_comptable")
            piece_nom = request.data.get("piece")
            exercice = request.data.get("exercice")
            mois = request.data.get("mois")
            info_supp_nouveau = request.data.get("info_supp")
            # Récupération de la pièce et du poste comptable
            poste_comptable = Poste_comptable.objects.get(nom_poste=poste_comptable_nom)
            piece = Piece.objects.get(nom_piece=piece_nom)
            # Chercher la dernière version du document existant avec le même info_supp
            documents_existants = Document.objects.filter(
                piece=piece,
                exercice=exercice,
                mois=mois
            )
            # Extraire les documents avec le même info_supp
            documents_meme_info = [
                doc for doc in documents_existants
                if len(doc.nom_fichier.split(", ")) > 1 and doc.nom_fichier.split(", ")[1] == info_supp_nouveau
            ]
            if documents_meme_info:
                # Récupérer la version max
                version = max(doc.version for doc in documents_meme_info) + 1
            else:
                version = 1
            # Créer le nouveau document avec la version correcte
            document = Document(
                nom_fichier=f"{request.data.get('nom_fichier')}, {info_supp_nouveau}",
                type=request.data.get("type_fichier"),
                contenu=contenu.read(),
                date_arrivee=request.data.get("date_arrivee"),
                poste_comptable=poste_comptable,
                piece=piece,
                exercice=exercice,
                mois=mois,
                version=version,
            )
            document.save()
            return JsonResponse({"id_fichier": document.id, "version": document.version})

        # Ce script sert a telecharger document
        elif request.data.get("action") == 'telecharger_document':
            import mimetypes
            import urllib.parse

            # Récupérer l'ID du document
            id_doc = request.data.get('id_document')
            if not id_doc:
                return JsonResponse({"error": "ID document manquant"}, status=400)

            # Chercher le document
            try:
                document = Document.objects.get(pk=id_doc)
            except Document.DoesNotExist:
                return JsonResponse({"error": "Document introuvable"}, status=404)

            # Contenu et nom du fichier
            file_content = document.contenu  # BinaryField
            file_name = document.nom_fichier.split(', ')[0]  # On prend le premier nom si plusieurs
            quoted_name = urllib.parse.quote(file_name)      # encode UTF-8

            # Détecter le type MIME selon l'extension du fichier
            content_type, _ = mimetypes.guess_type(file_name)
            content_type = content_type or 'application/octet-stream'

            # Créer la réponse HTTP pour téléchargement
            response = HttpResponse(file_content, content_type=content_type)
            response['Content-Disposition'] = f"attachment; filename=\"{file_name}\"; filename*=UTF-8''{quoted_name}"

            # Exposer le header Content-Disposition pour que fetch() puisse le lire
            response["Access-Control-Expose-Headers"] = "Content-Disposition"

            return response

        # Ce script sert a rechercher un document (Non utilisé)
        elif request.data.get('action') == 'rechercher_un_document':
            piece = request.data.get("piece", "").strip()
            poste_comptable = request.data.get("poste_comptable", "").strip()
            date = request.data.get("date", "").strip()
            mois = request.data.get("mois", "").strip()
            exercice = request.data.get("exercice", "").strip()

            # Dictionnaire de filtres dynamiques
            filters = {}

            if piece:
                filters["piece__icontains"] = Piece.objects.get(nom_piece=piece)
            if poste_comptable:
                filters["poste_comptable__nom_poste_comptable"] = "ESSAI"
                # filters["poste_comptable__nom_poste_comptable"] = "ESSAI"
            if date:
                filters["date_arrivee__icontains"] = date
            if mois:
                filters["mois__icontains"] = mois
            if exercice:
                filters["exercice__exact"] = exercice

            document = Document.objects.filter(**filters).select_related('poste_comptable', 'piece').values('piece__nom_piece', 'poste_comptable__nom_poste_comptable', 'poste_comptable__prenom_poste_comptable', 'nom_fichier', 'exercice', 'mois', 'date_arrivee')

            # Conversion JSON pour renvoyer à React
            return JsonResponse(list(document), safe=False)

        # Ce script va lister les documents pour un Auditeur
        elif request.data.get('action') == 'listes_documents_auditeur':

            # Récupérer tous les documents de l'utilisateur
            documents_qs = Document.objects.filter(
                poste_comptable__utilisateur_id=request.data.get('utilisateur')
            ).select_related('poste_comptable', 'piece').order_by('-id')

            # Construire un dictionnaire pour stocker la dernière version par document logique
            latest_docs = {}
            for doc in documents_qs:
                # Extraire info_supp (après la virgule)
                parts = doc.nom_fichier.split(', ')
                info_supp = parts[1] if len(parts) > 1 else ''

                key = (doc.piece.id, doc.exercice, doc.mois, info_supp)

                # Garde le document avec la version max pour ce key
                if key not in latest_docs or doc.version > latest_docs[key].version:
                    latest_docs[key] = doc

            # Préparer le résultat JSON
            result = []
            for doc in latest_docs.values():
                result.append({
                    'piece__nom_piece': doc.piece.nom_piece,
                    'poste_comptable__nom_poste': doc.poste_comptable.nom_poste,
                    'nom_fichier': doc.nom_fichier,
                    'type': doc.type,
                    'exercice': doc.exercice,
                    'mois': doc.mois,
                    'date_arrivee': doc.date_arrivee,
                    'version': doc.version
                })

            return JsonResponse(result, safe=False)

        # Ce script va lister les documents pour un Chef d'unite
        elif request.data.get('action') == 'listes_documents_chef_unite':

            # Récupérer tous les documents des postes comptables de la zone
            documents_qs = Document.objects.filter(
                poste_comptable__utilisateur__zone__nom_zone=request.data.get('zone')
            ).select_related('poste_comptable', 'piece').order_by('-id')

            # Construire un dictionnaire pour stocker la dernière version par document logique
            latest_docs = {}
            for doc in documents_qs:
                # Extraire info_supp (après la virgule)
                parts = doc.nom_fichier.split(', ')
                info_supp = parts[1] if len(parts) > 1 else ''

                key = (doc.piece.id, doc.exercice, doc.mois, info_supp)

                # Garde le document avec la version max pour ce key
                if key not in latest_docs or doc.version > latest_docs[key].version:
                    latest_docs[key] = doc

            # Préparer le résultat JSON
            result = []
            for doc in latest_docs.values():
                result.append({
                    'piece__nom_piece': doc.piece.nom_piece,
                    'poste_comptable__nom_poste': doc.poste_comptable.nom_poste,
                    'nom_fichier': doc.nom_fichier,
                    'type': doc.type,
                    'exercice': doc.exercice,
                    'mois': doc.mois,
                    'date_arrivee': doc.date_arrivee,
                    'version': doc.version
                })

            return JsonResponse(result, safe=False)

        # Ce script va lister les documents pour un Directeur
        elif request.data.get('action') == 'listes_documents_directeur':
            # Récupérer tous les documents
            documents_qs = Document.objects.all().select_related('poste_comptable', 'piece').order_by('-id')

            # Construire un dictionnaire pour stocker la dernière version par document logique
            latest_docs = {}
            for doc in documents_qs:
                # Extraire info_supp (après la virgule)
                parts = doc.nom_fichier.split(', ')
                info_supp = parts[1] if len(parts) > 1 else ''

                key = (doc.piece.id, doc.exercice, doc.mois, info_supp)

                # Garde le document avec la version max pour ce key
                if key not in latest_docs or doc.version > latest_docs[key].version:
                    latest_docs[key] = doc

            # Préparer le résultat JSON
            result = []
            for doc in latest_docs.values():
                result.append({
                    'piece__nom_piece': doc.piece.nom_piece,
                    'poste_comptable__nom_poste': doc.poste_comptable.nom_poste,
                    'nom_fichier': doc.nom_fichier,
                    'type': doc.type,
                    'exercice': doc.exercice,
                    'mois': doc.mois,
                    'date_arrivee': doc.date_arrivee,
                    'version': doc.version
                })

            return JsonResponse(result, safe=False)
        
        # Ce script va compter le nombre de domcuments generale par annee pour le tableau de bord
        elif request.data.get('action') == 'compter_nombre_documents_generale':
            nb_count = Document.objects.filter(exercice=datetime.now().year).count()
            return JsonResponse({'total_doc': nb_count})
        
        # Ce script va compter le nombre de domcuments par poste comptable et par annee pour le tableau de bord
        elif request.data.get('action') == 'compter_nombre_documents_par_poste_comptable':
            nb_count = Document.objects.filter(poste_comptable__nom_poste=request.data.get('poste_comptable'), exercice=request.data.get('exercice')).count()
            return JsonResponse({'total_doc': nb_count})

    # Ce script va afficher toutes les documents sans filtre (non utilisé)
    def get(self, request):
            document = Document.objects.all().select_related('poste_comptable', 'piece').values('piece__nom_piece', 'poste_comptable__nom_poste', 'nom_fichier', 'exercice', 'mois', 'date_arrivee')
            return JsonResponse(list(document), safe=False)


# Transcription
class TranscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    # Requete POST
    def post(self, request):

        # Ce script va ajouter une transcription des donnees
        if request.data.get('action') == 'ajouter_transcription':
            natures = request.data.get("natures")

            for nature in natures: 
                objet = request.data.get(nature) 

                try:
                    for i in objet:

                        if objet[i] != 0 and objet[i] != "":
                            montant =  float(objet[i])

                            Transcription.objects.create(
                                compte = Compte.objects.get(numero=i),
                                nature = nature,
                                montant = montant,
                                document_id = request.data.get('id_doc')
                            )

                except TypeError:

                    if objet != 0:
                        montant =  float(objet)

                        Transcription.objects.create(
                            nature = nature,
                            montant = montant,
                            document_id = request.data.get('id_doc')
                        )


            return JsonResponse({"succes": "Les données ont été transcrises avec succès"})
        
        # Ce script va ajouter une transcription pour une Balance (BOD/BOV)
        elif request.data.get('action') == 'ajouter_transcription_balance':
            fichier = request.FILES.get('fichier')
            df = pd.read_excel(fichier)

            df_melted = df.melt(
                id_vars=['EXERCICE', 'CLASSE', 'LECR_CPT_GENERAL', 'LECR_AUX'],
                var_name='NATURE',
                value_name='MONTANT'
            )

            # Filtrer les montants valides
            df_filtered = df_melted[df_melted['MONTANT'].notna() & (df_melted['MONTANT'] != 0)]
            balance = []
            for _, row in df_filtered.iterrows():
                compte_obj = Compte.objects.filter(numero=row['LECR_CPT_GENERAL']).first()
                if not compte_obj:
                    continue  # ignore si le compte n'existe pas
                balance.append(
                    Transcription(
                        document_id=request.data.get('document_id'),
                        nature=row['NATURE'],
                        montant=row['MONTANT'],
                        compte_id=compte_obj.id
                    )
                )

            Transcription.objects.bulk_create(balance)

            return JsonResponse({"succes": "Les données ont été transcrises avec succès"})

        # Ce script va recuperer les donnees transcrites
        elif request.data.get('action') == 'voir_detail_transcription':

            transcription = Transcription.objects.filter(
                document__piece__nom_piece=request.data.get('piece'), document__date_arrivee=request.data.get('date'),
                document__mois=request.data.get('mois'),
                document__exercice=request.data.get('exercice'),
                document__poste_comptable__nom_poste=request.data.get('poste_comptable'),
                document__version=request.data.get('version'),
               
                ).exclude(montant=0).values(
                    'compte__numero', 
                    'compte__classe',
                    'compte__libelle',
                    'document_id',
                    'nature',
                    'montant').order_by('compte__classe', 'compte__numero')

            return JsonResponse(list(transcription), safe=False)
        
        # Ce script va recuperer toutes les SJE derniere version dans la BD d'un poste comptable pour un exercice pour effectuer l'analyse
        elif request.data.get('action') == 'analyser_transcription_sje':
            piece_nom = request.data.get('piece')
            poste_nom = request.data.get('poste_comptable')
            exercice = request.data.get('exercice')

            # Récupérer les documents correspondants aux critères
            documents_qs = Document.objects.filter(
                piece__nom_piece=piece_nom,
                poste_comptable__nom_poste=poste_nom,
                exercice=exercice
            )

            # Construire un dictionnaire pour stocker la dernière version par document logique
            latest_docs = {}
            for doc in documents_qs:
                # Extraire info_supp (après la virgule)
                parts = doc.nom_fichier.split(', ')
                info_supp = parts[1] if len(parts) > 1 else ''

                key = (doc.piece.id, doc.exercice, doc.mois, info_supp)

                # Garde le document avec la version max pour ce key
                if key not in latest_docs or doc.version > latest_docs[key].version:
                    latest_docs[key] = doc

            # Récupérer les transcriptions liées aux documents de dernière version
            transcriptions = Transcription.objects.filter(
                document__in=latest_docs.values(),
                nature__in=['solde', 'report']
            ).values(
                'document__nom_fichier',
                'nature',
                'montant'
            )

            return JsonResponse(list(transcriptions), safe=False)

        # Ce script va recuperer les donnees utiles pour l'analyse de solde anormale
        elif request.data.get('action') == 'analyser_solde_anormale':

            base = Transcription.objects.filter(
                document__piece__nom_piece=request.data.get('piece'),
                document__poste_comptable__nom_poste=request.data.get('poste_comptable'),
                document__nom_fichier__icontains=request.data.get('proprietaire'),
                nature__icontains='sld',
                compte__classe__in=[4, 5],
                document__mois=request.data.get('mois'),
                document__exercice=request.data.get('exercice')
            )

            # 1) Sélection des dernières versions
            last_versions = (
                base.values('document__nom_fichier')
                    .annotate(latest_date=Max('document__date_arrivee'))
            )

            # 2) Filtrer à nouveau pour obtenir la ligne correspondant à la dernière version
            transcription = base.filter(
                document__date_arrivee__in=[lv['latest_date'] for lv in last_versions]
            ).values(
                'document__nom_fichier',
                'nature',
                'montant',
                'compte__numero',
                'compte__classe',
                'compte__solde_en_cours_exo',
                'document__date_arrivee'
            )

            return JsonResponse(list(transcription), safe=False)

        # Ce script va recuperer le nombre total de transcription par annee
        elif request.data.get('action') == 'compter_nombre_total_transcription':
            nb_count = Transcription.objects.filter(document__exercice=datetime.now().year).count()
            return JsonResponse({'total_transcription': nb_count})
        
        # Ce script va recuperer le nombre total de transcription par poste comptable et par annee
        elif request.data.get('action') == 'compter_nombre_total_transcription_par_poste_comptable':
            nb_count = Transcription.objects.filter(document__poste_comptable__nom_poste=request.data.get('poste_comptable'), document__exercice=request.data.get('exercice')).count()
            return JsonResponse({'total_transcription': nb_count})


    # Requete GET: Va recuperer toutes les transcriptions d'un TSDMT (non utilisé)
    def get(self, request):
        transcription = Transcription.objects.filter(document__piece__nom_piece='TSDMT')
        return JsonResponse(serializers.serialize('json', transcription), safe=False)


# Vue : TotalMontantTranscriptionFiltreeView
class TotalMontantTranscriptionFiltreeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        # Recuperer les donnees pour l'analyse de l'equilibre d'une balance
        if request.data.get('action') == 'analyse_equilibre_balance':

            base_queryset = Total_montant_transcription_filtrees.objects.filter(
                nom_poste=request.data.get('poste_comptable'),
                nom_piece=request.data.get('piece'),
                nom_fichier__icontains=request.data.get('proprietaire'),
                mois=request.data.get('mois'),
                exercice=request.data.get('exercice')
            )

            # Récupérer la date la plus recente par document
            last_versions = (
                base_queryset
                .values('nom_fichier')
                .annotate(latest_date=Max('date_arrivee'))
            )

            # Ne garder que les dernieres versions
            total = base_queryset.filter(
                date_arrivee__in=[lv['latest_date'] for lv in last_versions]
            ).values(
                'date_arrivee',
                'nom_fichier',
                'nature',
                'total'
            )

            return JsonResponse(list(total), safe=False)



        # if request.data.get('action') == 'analyse_equilibre_balance':

        #     total = Total_montant_transcription_filtrees.objects.filter(nom_poste=request.data.get('poste_comptable'), nom_piece=request.data.get('piece'), nom_fichier__icontains=request.data.get('proprietaire'), mois=request.data.get('mois'), exercice=request.data.get('exercice')).values('date_arrivee', 'nom_fichier', 'nature', 'total')
        #     return JsonResponse(list(total), safe=False)


        # if request.data.get('action') == 'verfication_solde_caisse':

        #     # Récupère le dernier jour du mois
        #     dernier_jour = calendar.monthrange(int(request.data.get('exercice')), int(request.data.get('mois')))[1]

        #     # Crée un objet date correspondant au dernier jour du mois
        #     date_sje = date(int(request.data.get('exercice')), int(request.data.get('mois')), dernier_jour)

        #     solde_balance = Total_montant_transcription_filtrees.objects.filter(nom_poste=request.data.get('poste_comptable'), nom_piece='BOD', nom_fichier__icontains=request.data.get('proprietaire'), mois=request.data.get('mois'), exercice=request.data.get('exercice'), nature__icontains='SLD_C').values('date_arrivee', 'nom_fichier', 'nature', 'total')
        #     encaisse_fin_du_mois_sje = Total_montant_transcription_filtrees.objects.filter(nom_poste=request.data.get('poste_comptable'), nom_piece='SJE', nature__icontains='solde', nom_fichier__icontains=date_sje).values('date_arrivee', 'nom_fichier', 'nature', 'total')

        #     return JsonResponse({'balance': list(solde_balance), 'sje': list(encaisse_fin_du_mois_sje)})

        if request.data.get('action') == 'verfication_solde_caisse':

            # Récupère le dernier jour du mois
            dernier_jour = calendar.monthrange(int(request.data.get('exercice')), int(request.data.get('mois')))[1]

            # Crée un objet date correspondant au dernier jour du mois
            date_sje = date(int(request.data.get('exercice')), int(request.data.get('mois')), dernier_jour)


            # RÉCUPÉRER LES ENREGISTREMENTS FILTRÉS (BOD)
            solde_balance_qs = Total_montant_transcription_filtrees.objects.filter(
                nom_poste=request.data.get('poste_comptable'),
                nom_piece='BOD',
                nom_fichier__icontains=request.data.get('proprietaire'),
                mois=request.data.get('mois'),
                exercice=request.data.get('exercice'),
                nature__icontains='SLD_C'
            )

            # Dictionnaire pour stocker la dernière version BOD
            latest_bod = {}

            for item in solde_balance_qs:
                # Extraction info_supp depuis nom_fichier
                parts = item.nom_fichier.split(', ')
                info_supp = parts[1] if len(parts) > 1 else ''

                key = (item.nom_piece, item.exercice, item.mois, info_supp)

                if key not in latest_bod or item.version > latest_bod[key].version:
                    latest_bod[key] = item

            # Construction de la réponse JSON BOD
            solde_balance = [{
                'date_arrivee': v.date_arrivee,
                'nom_fichier': v.nom_fichier,
                'nature': v.nature,
                'total': v.total
            } for v in latest_bod.values()]



            # RÉCUPÉRER LES ENREGISTREMENTS FILTRÉS (SJE)
            encaisse_sje_qs = Total_montant_transcription_filtrees.objects.filter(
                nom_poste=request.data.get('poste_comptable'),
                nom_piece='SJE',
                nature__icontains='solde',
                nom_fichier__icontains=date_sje,
            )

            # Dictionnaire pour stocker la dernière version SJE
            latest_sje = {}

            for item in encaisse_sje_qs:
                parts = item.nom_fichier.split(', ')
                info_supp = parts[1] if len(parts) > 1 else ''

                key = (item.nom_piece, item.exercice, item.mois, info_supp)

                if key not in latest_sje or item.version > latest_sje[key].version:
                    latest_sje[key] = item

            # Construction de la réponse JSON SJE
            encaisse_fin_du_mois_sje = [{
                'date_arrivee': v.date_arrivee,
                'nom_fichier': v.nom_fichier,
                'nature': v.nature,
                'total': v.total
            } for v in latest_sje.values()]


            # ========= 🔵 3. RETOUR =========
            return JsonResponse({
                'balance': solde_balance,
                'sje': encaisse_fin_du_mois_sje
            })


# Compte
class CompteView(APIView):
    # Requete POST
    def post(self, request):

        if request.data.get('action') == 'lister_tous_les_comptes':
            comptes = Compte.objects.all().values(
                'id',
                'classe',
                'poste',
                'rubrique',
                'numero',
                'libelle',
                'acte_reglementaire',
                'solde_en_cours_exo',
                'solde_fin_gest',
                'type',
                'proprietaire_id',
                'created_at',
                'updated_at',
                'proprietaire__nom_proprietaire',
            ).order_by('-id')
            return JsonResponse(list(comptes), safe=False)

        if request.data.get('action') == 'obtenir_nombre_total_comptes':
            nb_count = Compte.objects.count()
            return JsonResponse({'total_comptes': nb_count})

        if request.data.get('action') == 'get_comptes_regroupements':
            comptes = Compte.objects.filter(type='Regroupements').values('id', 'numero')
            # comptes_serialize = serializers.serialize('json', comptes)
            return JsonResponse(list(comptes), safe=False)
        
        elif request.data.get('action') == 'create':
            if request.data.get('compte_regroupement') != "":
                compte = Compte(
                    classe=request.data.get('classe'),
                    poste=request.data.get('poste'), 
                    rubrique=request.data.get('rubrique'),
                    numero = request.data.get('numero'),
                    libelle = request.data.get('libelle'),
                    acte_reglementaire=request.data.get('acte_reglementaire'),
                    solde_en_cours_exo=request.data.get('solde_en_cours_exo'),
                    solde_fin_gest=request.data.get('solde_fin_gest'),
                    type = request.data.get('type'),
                    proprietaire_id = request.data.get('proprietaire')
                )
                compte.save()
            else:
                compte = Compte(
                    numero = request.data.get('numero'),
                    libelle = request.data.get('libelle'),
                    type = request.data.get('type')
                )
                compte.save()
            return JsonResponse({"succes": "Le compte a été ajouté avec succès"})
        
        # return HttpResponse({"message": None})
            

    # Requete PUT
    def put(self, request):
        compte = Compte.objects.get(id=request.data.get('id'))
        compte.classe = request.data.get('classe')
        compte.poste = request.data.get('poste')
        compte.rubrique = request.data.get('rubrique')
        compte.numero = request.data.get('numero')
        compte.libelle = request.data.get('libelle')
        compte.acte_reglementaire = request.data.get('acte_reglementaire')
        compte.solde_en_cours_exo = request.data.get('solde_en_cours_exo')
        compte.solde_fin_gest = request.data.get('solde_fin_gest')
        compte.type = request.data.get('type')
        compte.proprietaire_id = request.data.get('proprietaire')
        compte.save()
        return JsonResponse({'succes': 'Le compte a été modifié avec succès'})

    # Requete DELETE
    def delete(self, request):
        compte = Compte.objects.get(id=request.data.get('id'))
        compte.delete()
        return JsonResponse({'succes': 'Le compte a été supprimé avec succès'})

    # Requete GET
    def get(self, request):
        comptes = Compte.objects.all().values('numero')
        # comptes_serialize = serializers.serialize('json', comptes)
        return JsonResponse(list(comptes), safe=False)


# Anomalie
class AnomalieView(APIView):
    permission_classes = [IsAuthenticated]

    # Requete POST
    def post(self, request):

        # Ajouter une anomalie
        if request.data.get('action') == 'ajouter_anomalie':
            data = request.data.get('data') or []  # Toujours une liste
            type_analyse = request.data.get('type_analyse')
            poste_comptable = request.data.get('poste_comptable')
            exercice = request.data.get('exercice')
            inserted = 0
            skipped = 0
            # Extraire les descriptions envoyées
            descriptions_envoyees = [
                item.get('description')
                for item in data
                if item.get('description')
            ]
            if type_analyse == 'report_sje':
                # MARQUER COMME RÉSOLUE selon type_analyse + poste_comptable
                anomalies_a_resoudre = Anomalie.objects.filter(
                    type_analyse=type_analyse,
                    document__poste_comptable__nom_poste=poste_comptable,
                    document__exercice=exercice
                ).distinct()
            else:
                # MARQUER COMME RÉSOLUE selon type_analyse + poste_comptable
                anomalies_a_resoudre = Anomalie.objects.filter(
                    type_analyse=type_analyse,
                    document__poste_comptable__nom_poste=poste_comptable,
                    document__mois=request.data.get('mois'),
                    document__piece__nom_piece=request.data.get('piece'),
                    document__nom_fichier__icontains=request.data.get('proprietaire'),
                    document__exercice=exercice
                ).distinct()
            # Si data contient des anomalies, on exclut celles envoyées
            if descriptions_envoyees:
                anomalies_a_resoudre = anomalies_a_resoudre.exclude(
                    description__in=descriptions_envoyees
                )
            # Résolution
            for anomalie in anomalies_a_resoudre:
                if anomalie.statut != "Résolue":
                    anomalie.statut = "Résolue"
                    anomalie.save()

                    # Ajouter automatiquement une correction
                    Correction.objects.create(
                        anomalie=anomalie,
                        commentaire="Mise à jour du pièce justificative"
                    )
            # TRAITER LES NOUVELLES ANOMALIES
            for item in data:
                date_str = item.get('date')
                description = item.get('description')
                fichier_noms = item.get('fichier', [])
                type_analyse_item = item.get('analyse', type_analyse)
                if not description or not date_str:
                    skipped += 1
                    continue
                try:
                    date_anomalie = datetime.strptime(date_str, "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    skipped += 1
                    continue
                anomalie, created = Anomalie.objects.get_or_create(
                    description=description,
                    type_analyse=type_analyse_item,
                    defaults={
                        "date_anomalie": date_anomalie,
                        "statut": "Nouvelle",
                    }
                )
                # Ajouter les documents liés à l'anomalie
                for nom in fichier_noms:
                    try:
                        doc = Document.objects.get(
                            nom_fichier=nom,
                            poste_comptable__nom_poste=poste_comptable
                        )
                        anomalie.document.add(doc)
                    except Document.DoesNotExist:
                        print(f"Document non trouvé pour poste_comptable {poste_comptable} : {nom}")
                if created:
                    inserted += 1
                else:
                    skipped += 1
            return Response(
                {"status": "ok", "inserted": inserted, "skipped": skipped},
                status=status.HTTP_200_OK
            )

        
        elif request.data.get('action') == 'exporter_rapport':
            anomalie_id = request.data.get('anomalie')

            mois_en_lettres = {
                "01": "Janvier",
                "02": "Février",
                "03": "Mars",
                "04": "Avril",
                "05": "Mai",
                "06": "Juin",
                "07": "Juillet",
                "08": "Août",
                "09": "Septembre",
                "10": "Octobre",
                "11": "Novembre",
                "12": "Décembre"
            }

            # 🔧 CORRECTIF ENCODAGE FPDF
            def clean_text(text):
                if text is None:
                    return ""
                return (
                    str(text)
                    .replace("\u202f", " ")  # espace insécable fine
                    .replace("\u00a0", " ")  # espace insécable
                )

            try:
                anomalie = Anomalie.objects.get(pk=anomalie_id)
            except Anomalie.DoesNotExist:
                return JsonResponse({"error": "Anomalie introuvable"}, status=404)

            documents = anomalie.document.all()

            if documents.exists():
                code_poste = getattr(documents[0].poste_comptable, "code_poste", "N/A")
                nom_poste = getattr(documents[0].poste_comptable, "nom_poste", "N/A")
                lieu = getattr(documents[0].poste_comptable, "lieu", "N/A")
                poste = getattr(documents[0].poste_comptable, "poste", "N/A")
                responsable = getattr(documents[0].poste_comptable, "responsable", "N/A")
            else:
                code_poste = nom_poste = lieu = poste = responsable = "N/A"

            # Génération PDF
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()

            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, clean_text("RAPPORT D'ANOMALIE"), ln=True, align='C')

            pdf.ln(5)
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 8, clean_text(f"Date anomalie : {anomalie.date_anomalie}"), ln=True)
            pdf.cell(
                200,
                8,
                clean_text(f"Type d'analyse : {anomalie.type_analyse.replace('_', ' ').upper()}"),
                ln=True
            )
            pdf.multi_cell(
                0,
                8,
                clean_text(f"Description : {anomalie.description or 'Aucune'}")
            )
            pdf.cell(200, 8, clean_text(f"Statut : {anomalie.statut}"), ln=True)

            pdf.ln(10)
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 8, clean_text(f"Poste comptable concerné : {nom_poste}"), ln=True)
            pdf.cell(0, 8, clean_text(f"Code poste : {code_poste}"), ln=True)
            pdf.cell(0, 8, clean_text(f"Lieu : {lieu}"), ln=True)
            pdf.cell(0, 8, clean_text(f"Poste : {poste}"), ln=True)
            pdf.cell(0, 8, clean_text(f"Responsable : {responsable}"), ln=True)

            pdf.ln(10)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(200, 10, clean_text("Documents liés :"), ln=True)

            col1_width = 20
            col2_width = 115
            col3_width = 35
            col4_width = 20
            row_height = 8

            pdf.set_font("Arial", "B", 11)
            pdf.cell(col1_width, row_height, "Pièce", border=1, align="C")
            pdf.cell(col2_width, row_height, "Nom du fichier", border=1, align="C")
            pdf.cell(col3_width, row_height, "Mois", border=1, align="C")
            pdf.cell(col4_width, row_height, "Exercice", border=1, align="C")
            pdf.ln(row_height)

            pdf.set_font("Arial", "", 11)
            for doc in documents:
                piece = getattr(doc.piece, "nom_piece", "N/A")
                nom_fichier = doc.nom_fichier
                mois_chiffre = doc.mois or "N/A"
                mois = mois_en_lettres.get(mois_chiffre.zfill(2), "N/A")
                exercice = doc.exercice or "N/A"

                pdf.cell(col1_width, row_height, clean_text(piece), border=1, align="C")
                pdf.cell(col2_width, row_height, clean_text(nom_fichier), border=1)
                pdf.cell(col3_width, row_height, clean_text(mois), border=1, align="C")
                pdf.cell(col4_width, row_height, clean_text(exercice), border=1, align="C")
                pdf.ln(row_height)

            pdf_output = pdf.output(dest='S').encode('latin-1')

            response = HttpResponse(pdf_output, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="rapport_anomalie.pdf"'

            return response

                
        #Changer le statut des anomalies en cours
        elif(request.data.get('action') == 'changer_statut_anomalie_en_cours'):
            anomalies = request.data.get('anomalies')

            for id_anomalie in anomalies:
                anomalie = Anomalie.objects.get(id=id_anomalie)
                anomalie.statut = 'En cours'
                anomalie.save()
                
            return JsonResponse({'succes': str(anomalies.__len__()) + " anomalie(s) traitée(s)"})

        # Compter le nombre total des anomalies
        elif(request.data.get('action') == 'compter_nombre_anomalies_generale'):
            nb_anomalies = Anomalie.objects.filter(document__exercice=datetime.now().year).count()
            return JsonResponse({'total_anomalies': nb_anomalies})
        
        # Compter le nombre total des anomalies par poste comptable et par annee
        elif(request.data.get('action') == 'compter_nombres_anomalies_par_poste_comptable'):
            nb_anomalies = Anomalie.objects.filter(document__poste_comptable__nom_poste=request.data.get('poste_comptable'), document__exercice=request.data.get('exercice')).count()
            return JsonResponse({'total_anomalies': nb_anomalies})
        

        # Compter le nombre total des anomalies resolues
        elif(request.data.get('action') == 'compter_nombre_anomalies_resolu'):
            nb_anomalies_resolu = Anomalie.objects.filter( Q(statut__icontains='résolu') | Q(statut__icontains='resolu'), document__exercice=datetime.now().year).count()
            return JsonResponse({'total_anomalies_resolu': nb_anomalies_resolu})
        

        # Compter le nombre des anomalies resolues par poste comptable et par annee
        elif request.data.get('action') == 'compter_nombres_anomalies_resolu_par_poste_comptables':
            nb_anomalies_resolu = Anomalie.objects.filter( Q(statut__icontains='résolu') | Q(statut__icontains='resolu'), document__poste_comptable__nom_poste=request.data.get('poste_comptable'), document__exercice=request.data.get('exercice')).count()
            return JsonResponse({'total_anomalies_resolu': nb_anomalies_resolu})


        # Cette vue va compter les nombres d'anomalies detectees par mois
        elif(request.data.get('action') == 'recuperer_nombre_anomalies_par_mois'):
            anomalies = []
            all_month = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
            for month in all_month:
                nb_anomalies = Anomalie.objects.filter(created_at__month=month, created_at__year=datetime.now().year).count()
                anomalies.append(nb_anomalies)
               
            return JsonResponse(list(anomalies), safe=False)
        

        # Cette vue va compter les nombres d'anomalies par mois par poste comptable et par annee
        elif(request.data.get('action') == 'recuperer_nombre_anomalies_par_mois_par_comptable'):
            anomalies = []
            all_month = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
            for month in all_month:
                nb_anomalies = Anomalie.objects.filter(created_at__month=month, document__poste_comptable__nom_poste=request.data.get('poste_comptable'), created_at__year=request.data.get('exercice')).count()
                anomalies.append(nb_anomalies)
               
            return JsonResponse(list(anomalies), safe=False)


        #Cette vue va compter les nombres d'anomalies resolues par mois
        elif request.data.get('action') == 'recuperer_nombres_anomalies_resolues_par_mois':
            anomalies = []
            all_month = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
            for month in all_month:
                nb_anomalies = Anomalie.objects.filter( Q(statut__icontains='résolu') | Q(statut__icontains='resolu'), created_at__month=month, created_at__year=datetime.now().year).count()
                anomalies.append(nb_anomalies)
                # print('nombre', nb_anomalies)
            return JsonResponse(list(anomalies), safe=False)


        #Cette vue va compter les nombres d'anomalies resolues par mois par poste comptable et par annee
        elif request.data.get('action') == 'recuperer_nombres_anomalies_resolues_par_mois_par_poste_comptable':
            anomalies = []
            all_month = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
            for month in all_month:
                nb_anomalies = Anomalie.objects.filter( Q(statut__icontains='résolu') | Q(statut__icontains='resolu'), created_at__month=month, document__poste_comptable__nom_poste=request.data.get('poste_comptable'), created_at__year=request.data.get('exercice')).count()
                anomalies.append(nb_anomalies)
                # print('nombre', nb_anomalies)
            return JsonResponse(list(anomalies), safe=False)

        # Liste des anomalies pour un auditeur
        elif request.data.get('action') == 'lister_les_anomalies_pour_un_auditeur':

            utilisateur_id = request.data.get('utilisateur_id')

            anomalies = (
                Anomalie.objects
                .filter(document__poste_comptable__utilisateur_id=utilisateur_id)
                .annotate(
                    fichiers=ArrayAgg(
                        F('document__nom_fichier'),
                        distinct=True
                    )
                )
                .values(
                    'id',
                    'date_anomalie',
                    'document__poste_comptable__nom_poste',
                    'document__exercice',
                    'description',
                    'statut',
                    'type_analyse',
                    'created_at',
                    'fichiers'
                )
            )

            return JsonResponse(list(anomalies), safe=False)
        
        # Liste des anomalies pour un chef d'unite
        elif request.data.get('action') == 'lister_des_aomalies_pour_un_chef_unite':

            zone = request.data.get('zone')

            anomalies = (
                Anomalie.objects
                .filter(document__poste_comptable__utilisateur__zone__nom_zone=zone)
                .annotate(
                    fichiers=ArrayAgg(
                        F('document__nom_fichier'),
                        distinct=True
                    )
                )
                .values(
                    'id',
                    'date_anomalie',
                    'document__poste_comptable__nom_poste',
                    'document__exercice',
                    'description',
                    'statut',
                    'type_analyse',
                    'created_at',
                    'fichiers'
                )
            )

            return JsonResponse(list(anomalies), safe=False)



    # Requete GET Renvoyer toutes les anomalies (Pour un directeur)
    def get(self, request):
        # Optionnel : renvoyer toutes les anomalies
        anomalies = Anomalie.objects.annotate(
            fichiers=ArrayAgg(
                F('document__nom_fichier'),
                distinct=True
            )
        ).values(
            'id',
            'date_anomalie',
            'document__poste_comptable__nom_poste',
            'document__exercice',
            'description',
            'statut',
            'type_analyse',
            'created_at',
            'fichiers'
        ).order_by('id')
            
        return Response(list(anomalies))


# Correction
class CorrectionView(APIView):

    # Requete POST
    def post(self, request):

        # Ce script va ajouter une correction d'une anomalie
        if(request.data.get('action') == 'ajouter_correction'):

            correction = Correction(
                commentaire = request.data.get('commentaire'),
                anomalie_id = request.data.get('anomalie')
            ) 

            anomalie = Anomalie.objects.get(id=request.data.get('anomalie'))
            anomalie.statut = 'Résolue'

            correction.save()
            anomalie.save()

            return JsonResponse({"succes": "L'anomalie est considerée comme résolue"})

        # Ce script va afficher la correction d'une anomalie selectionné
        elif request.data.get('action') == 'voir_detail_resolution_anomalie':
            resolution = Correction.objects.filter(anomalie_id=request.data.get('anomalie')).values('commentaire', 'created_at')
            return JsonResponse(list(resolution), safe=False)