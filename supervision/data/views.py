from django.shortcuts import render
from django.core import serializers
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from .models import Piece, Document, Transcription, Compte, PieceCompte, Trace, Anomalie, Total_montant_transcription_filtrees, Correction
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from users.models import Poste_comptable
from datetime import datetime
import json
import pandas as pd

import calendar
from datetime import date


# Create your views here.
def index(request):
    fichiers = Document.objects.all()
    f = open("test.pdf", 'wb')
    f.write(fichiers[0].contenu)
    f.close()
    # json = serializers.serialize("json", fichiers)
    return HttpResponse(fichiers[0].contenu)


# class CompteView(APIView):
#     def get(self, request):
#         comptes = Compte.objects.all().values('numero')
#         return JsonResponse(list(comptes), safe=False)


# @api_view(['POST'])
# Piece
class PieceView(APIView):
    def post(self, request):
        
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


    def get(self, request):
        pieces = Piece.objects.all().order_by('nom_piece')
        pieces_serialize = serializers.serialize('json', pieces)
        return JsonResponse(json.loads(pieces_serialize), safe=False)
    

# Liaison piece - compte
class PieceCompteView(APIView):

    def post(self, request):
        if request.data.get("action") == 'ajouter':
            nature = request.data.get('nature')

            piece_et_compte = PieceCompte(
                piece_id = request.data.get('piece'),
                compte = Compte.objects.get(numero=request.data.get('compte')),
                nature = ", ".join(nature)
            )

            piece_et_compte.save()

            return JsonResponse({'succes': 'La liaison entre le compte et la pièce a ete établie avec succès'})
        
        elif request.data.get("action") == "filtrer_liaison":
            # piece_et_compte = PieceCompte.objects.filter(nature__icontains=request.data.get('nature')).select_related('compte').distinct().values('compte__numero')
            piece_et_compte = PieceCompte.objects.filter(piece=Piece.objects.get(nom_piece=request.data.get('piece'))).select_related('compte').distinct().values('compte__numero', 'nature')

            return JsonResponse(list(piece_et_compte), safe=False)
    

    def put(self, request):
        nature = request.data.get('nature')

        piece_compte = PieceCompte.objects.get(pk=request.data.get('id'))

        piece_compte.piece_id = request.data.get('piece')
        piece_compte.compte = Compte.objects.get(numero=request.data.get('compte'))
        piece_compte.nature = ', '.join(nature)

        piece_compte.save()

        return JsonResponse({'succes': 'Modification éffectuée avec succès'})


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
    def post(self, request):

        if request.data.get("action") == 'ajouter_un_document':
            contenu = request.FILES.get("fichier")
            poste_comptable = request.data.get("poste_comptable")
            # poste_comptable_list = poste_comptable.split(" ")

            document = Document(
                nom_fichier = request.data.get("nom_fichier") + ", " + request.data.get("info_supp"),
                type = request.data.get("type_fichier"),
                contenu = contenu.read(),
                date_arrivee = request.data.get("date_arrivee"),
                poste_comptable = Poste_comptable.objects.get(nom_poste=poste_comptable),
                piece = Piece.objects.get(nom_piece=request.data.get("piece")),
                exercice = request.data.get("exercice"),
                mois = request.data.get("mois"),
            )
            document.save()
            # print(request.data.get('nom_fichier'))
            return JsonResponse({"id_fichier": document.id})
        
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
    
        elif request.data.get('action') == 'listes_documents_auditeur':
            document = Document.objects.all().select_related('poste_comptable', 'piece').filter(poste_comptable__utilisateur_id=request.data.get('utilisateur')).values('piece__nom_piece', 'poste_comptable__nom_poste', 'nom_fichier', 'exercice', 'mois', 'date_arrivee')
            return JsonResponse(list(document), safe=False)
            
        elif request.data.get('action') == 'listes_documents_chef_unite':
            document = Document.objects.all().select_related('poste_comptable', 'piece').filter(poste_comptable__utilisateur__zone__nom_zone=request.data.get('zone')).values('piece__nom_piece', 'poste_comptable__nom_poste', 'nom_fichier', 'exercice', 'mois', 'date_arrivee')
            return JsonResponse(list(document), safe=False)
        
        elif request.data.get('action') == 'listes_documents_directeur':
            document = Document.objects.all().values('piece__nom_piece', 'poste_comptable__nom_poste', 'nom_fichier', 'exercice', 'mois', 'date_arrivee')
            return JsonResponse(list(document), safe=False)

        elif request.data.get('action') == 'compter_nombre_documents_generale':
            nb_count = Document.objects.count()
            return JsonResponse({'total_doc': nb_count})

    def get(self, request):
            document = Document.objects.all().select_related('poste_comptable', 'piece').values('piece__nom_piece', 'poste_comptable__nom_poste', 'nom_fichier', 'exercice', 'mois', 'date_arrivee')
            return JsonResponse(list(document), safe=False)


class TranscriptionView(APIView):
    def post(self, request):
        if request.data.get('action') == 'ajouter_transcription':
            natures = request.data.get("natures")

            for nature in natures: 
                objet = request.data.get(nature) 

                try:
                    for i in objet:

                        if objet[i] != 0:
                            montant =  float(objet[i])

                        # else:
                        #     montant = 0

                            Transcription.objects.create(
                                compte = Compte.objects.get(numero=i),
                                nature = nature,
                                montant = montant,
                                document_id = request.data.get('id_doc')
                            )

                except TypeError:

                    if objet != 0:
                        montant =  float(objet)

                    # else:
                    #     montant = 0

                        Transcription.objects.create(
                            nature = nature,
                            montant = montant,
                            document_id = request.data.get('id_doc')
                        )
            Trace.objects.create(
                utilisateur_id = request.data.get('utilisateur'),
                action = f"a transcrit une pièce - {request.data.get('piece')}",
            )

            return JsonResponse({"succes": "Les données ont été transcrises avec succès"})
        
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

        
        elif request.data.get('action') == 'voir_detail_transcription':

            transcription = Transcription.objects.filter(
                document__piece__nom_piece=request.data.get('piece'), document__date_arrivee=request.data.get('date'),
                document__mois=request.data.get('mois'),
                document__exercice=request.data.get('exercice'),
                document__poste_comptable__nom_poste = request.data.get('poste_comptable'),
               
                ).exclude(montant=0).values(
                    'compte__numero', 
                    'compte__libelle', 
                    'nature',
                    'montant').order_by('nature')

            return JsonResponse(list(transcription), safe=False)
        
        elif request.data.get('action') == 'analyser_transcription_sje':
            transcription = Transcription.objects.filter(document__piece__nom_piece=request.data.get('piece'), document__poste_comptable__nom_poste=request.data.get('poste_comptable'), document__exercice=request.data.get('exercice'), nature__in=['solde', 'report']).values('document__nom_fichier', 'nature', 'montant')
            return JsonResponse(list(transcription), safe=False)


    def get(self, request):
        transcription = Transcription.objects.filter(document__piece__nom_piece='TSDMT')
        return JsonResponse(serializers.serialize('json', transcription), safe=False)


class TotalMontantTranscriptionFiltreeView(APIView):
    def post(self, request):
        if request.data.get('action') == 'analyse_equilibre_balance':
            total = Total_montant_transcription_filtrees.objects.filter(nom_poste=request.data.get('poste_comptable'), nom_piece=request.data.get('piece'), mois=request.data.get('mois'), exercice=request.data.get('exercice')).values('date_arrivee', 'nom_fichier', 'nature', 'total')
            return JsonResponse(list(total), safe=False)
        
        if request.data.get('action') == 'verfication_solde_caisse':
            # Récupère le dernier jour du mois
            dernier_jour = calendar.monthrange(int(request.data.get('exercice')), int(request.data.get('mois')))[1]
            # Crée un objet date correspondant au dernier jour du mois
            date_sje = date(int(request.data.get('exercice')), int(request.data.get('mois')), dernier_jour)
            solde_balance = Total_montant_transcription_filtrees.objects.filter(nom_poste=request.data.get('poste_comptable'), nom_piece='BOD', mois=request.data.get('mois'), exercice=request.data.get('exercice'), nature__icontains='SLD_C').values('date_arrivee', 'nom_fichier', 'nature', 'total')
            encaisse_fin_du_mois_sje = Total_montant_transcription_filtrees.objects.filter(nom_poste=request.data.get('poste_comptable'), nom_piece='SJE', nature__icontains='solde', nom_fichier__icontains='2025-11-04').values('date_arrivee', 'nom_fichier', 'nature', 'total')
            return JsonResponse({'balance': list(solde_balance), 'sje': list(encaisse_fin_du_mois_sje)})


class CompteView(APIView):
    def post(self, request):
        if request.data.get('action') == 'get_comptes_regroupements':
            comptes = Compte.objects.filter(type='Regroupements').values('id', 'numero')
            # comptes_serialize = serializers.serialize('json', comptes)
            return JsonResponse(list(comptes), safe=False)
        elif request.data.get('action') == 'create':
            if request.data.get('compte_regroupement') != "":
                compte = Compte(
                    numero = request.data.get('numero'),
                    libelle = request.data.get('libelle'),
                    type = request.data.get('type'),
                    compte_regroupement_id = request.data.get('compte_regroupement')
                )
                compte.save()
            else:
                compte = Compte(
                    numero = request.data.get('numero'),
                    libelle = request.data.get('libelle'),
                    type = request.data.get('type')
                )
                compte.save()
            return JsonResponse({"message": "Ajout effectuee avec succes"})
        return HttpResponse({"message": None})
            

    def get(self, request):
        comptes = Compte.objects.all().values('numero')
        # comptes_serialize = serializers.serialize('json', comptes)
        return JsonResponse(list(comptes), safe=False)


class TraceView(APIView):
    def get(self, request):
        traces = Trace.objects.all().values('id', 'utilisateur_id', 'utilisateur__nom', 'utilisateur__prenom', 'action', 'created_at').order_by('id')
        return JsonResponse(list(traces), safe=False)
    

class AnomalieView(APIView):

    def post(self, request):

        if(request.data.get('action') == 'ajouter_anomalie'):
            data = request.data.get('data')  # DRF parse automatiquement le JSON
            inserted = 0
            skipped = 0

            for item in data:
                date_str = item.get('date')
                description = item.get('description')
                fichier_nom = item.get('fichier')

                # Conversion de la date string en objet date
                try:
                    date_anomalie = datetime.strptime(date_str, "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    skipped += 1
                    continue  # ignore si la date n'est pas valide

                # Récupération du document
                try:
                    document = Document.objects.get(nom_fichier=fichier_nom)  # adapter le champ 'nom' si nécessaire
                except Document.DoesNotExist:
                    skipped += 1
                    continue  # ignore si le document n'existe pas

                # Vérifier si le document a déjà une anomalie
                if not hasattr(document, 'anomalie'):
                    Anomalie.objects.create(
                        date_anomalie=date_anomalie,
                        document=document,
                        description=description,
                        statut="Nouveau"  # valeur par défaut
                    )
                    inserted += 1
                else:
                    skipped += 1

            return Response({
                "status": "ok",
                "inserted": inserted,
                "skipped": skipped
            }, status=status.HTTP_200_OK)
    
        elif(request.data.get('action') == 'changer_statut_anomalie_en_cours'):
            anomalies = request.data.get('anomalies')

            for id_anomalie in anomalies:
                anomalie = Anomalie.objects.get(id=id_anomalie)
                anomalie.statut = 'En cours'
                anomalie.save()
                
            return JsonResponse({'succes': str(anomalies.__len__()) + " anomalie(s) traitée(s)"})

        elif(request.data.get('action') == 'compter_nombre_anomalies_generale'):
            nb_anomalies = Anomalie.objects.count()
            return JsonResponse({'total_anomalies': nb_anomalies})
        
        elif(request.data.get('action') == 'compter_nombre_anomalies_resolu'):
            nb_anomalies_resolu = Anomalie.objects.filter( Q(statut__icontains='résolu') | Q(statut__icontains='resolu')).count()
            return JsonResponse({'total_anomalies_resolu': nb_anomalies_resolu})
        
        elif(request.data.get('action') == 'recuperer_nombre_anomalies_par_mois'):
            anomalies = []
            all_month = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
            for month in all_month:
                nb_anomalies = Anomalie.objects.filter(created_at__month=month).count()
                anomalies.append(nb_anomalies)
                # print('nombre', nb_anomalies)
            return JsonResponse(list(anomalies), safe=False)

    def get(self, request):
        # Optionnel : renvoyer toutes les anomalies
        anomalies = Anomalie.objects.all().values(
            'id', 
            'date_anomalie', 
            'description', 
            'statut' , 
            'document__poste_comptable__nom_poste', 
            'document__exercice',
            'created_at',
        ).order_by('id')
        return Response(list(anomalies))


class CorrectionView(APIView):
    def post(self, request):

        if(request.data.get('action') == 'ajouter_correction'):

            correction = Correction(
                commentaire = request.data.get('commentaire'),
                anomalie_id = request.data.get('anomalie')
            ) 

            anomalie = Anomalie.objects.get(id=request.data.get('anomalie'))
            anomalie.statut = 'Résolu'

            correction.save()
            anomalie.save()

            return JsonResponse({"succes": "L'anomalie est considerée comme résolu"})