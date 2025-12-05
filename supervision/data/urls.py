from django.urls import path
from  . import views

urlpatterns = [
    # path('', views.index, name='index'),

    # Url - Proprietaire
    path('proprietaire/get', views.ProprietaireView.as_view(), name='obtenir_la_liste_des_proprietaires'),

    # Url - Piece
    path('piece/create', views.PieceView.as_view(), name='create_piece'),
    path('piece/get_pieces', views.PieceView.as_view(), name='get_pieces'),
    path('piece/update', views.PieceView.as_view(), name='update_piece'),
    path('piece/delete', views.PieceView.as_view(), name='delete_piece'),
    path('piece/periode', views.PieceView.as_view(), name='recuperer_la_periode_la_piece'),

    # Url - Exercice
    path('exercice/create', views.ExerciceView.as_view(), name='creer_exercice'),
    path('exercice/get', views.ExerciceView.as_view(), name='liste_exercices'),

    # Url - Document
    path('document/save', views.DocumentView.as_view(), name='save_document'),
    path('document/liste', views.DocumentView.as_view(), name='liste_document'),
    path('document/rechercher', views.DocumentView.as_view(), name='rechercher_un_document'),
    path('document/count', views.DocumentView.as_view(), name='compter_le_nombre_de_document_generale'),
    path('document/telecharger', views.DocumentView.as_view(), name='telecharger_un_document'),

    # Transcription
    path('transcription/create', views.TranscriptionView.as_view(), name='create_transcription'),
    path('transcription/liste', views.TranscriptionView.as_view(), name='liste_transcription'),
    path('transcription/data_analyse', views.TranscriptionView.as_view(), name='analyser_transcription_par_type'),

    # Url - Liaison Piece - Compte
    path('piece_compte/creer', views.PieceCompteView.as_view(), name='creer_liaison_piece_compte'),
    path('piece_compte/modifier', views.PieceCompteView.as_view(), name='modifier_liaison_piece_compte'),
    path('piece_compte/lister', views.PieceCompteView.as_view(), name='lister_liaison_piece_compte'),
    path('piece_compte/liste_liaison_pour_une_piece', views.PieceCompteView.as_view(), name='liste_liaison_pour_une_piece'),
    
    # Url - compte
    path('compte/create', views.CompteView.as_view(), name='create_compte'),
    path('compte/update', views.CompteView.as_view(), name='update_compte'),
    path('compte/delete', views.CompteView.as_view(), name='delete_compte'),
    path('compte/get_comptes', views.CompteView.as_view(), name='get_comptes'),
    path('compte/get_comptes_regroupements', views.CompteView.as_view(), name='get_comptes'),
    path('compte/get_number', views.CompteView.as_view(), name='get_number_compte'),

    # Url - anomalie
    path('anomalie/insert', views.AnomalieView.as_view(), name='inserer_des_anomalies'),
    path('anomalie/liste', views.AnomalieView.as_view(), name='lister_des_anomalies'),
    path('anomalie/change_state', views.AnomalieView.as_view(), name='change_le_statut_des_anomalies'),
    path('anomalie/count', views.AnomalieView.as_view(), name='lister_des_anomalies'),
    path('anomalie/rapport', views.AnomalieView.as_view(), name='exporter_rapport_anomalie'),

    # Url - Recuperer des donnees pour les analyses : equilibre balance et solde caisse
    path('analyse/equilibre_balance', views.TotalMontantTranscriptionFiltreeView.as_view(), name='obtenir_les_donnees_pour_analyse_equilibre_balance'),
    path('analyse/solde_caisse', views.TotalMontantTranscriptionFiltreeView.as_view(), name='obtenir_les_donnees_pour_analyse_solde_caisse'),

    # Url - correction
    path('correction/insert', views.CorrectionView.as_view(), name='ajouter_une_correction_d_anomalie'),
    path('correction/voir_detail', views.CorrectionView.as_view(), name='voir_detail_resolution_anomalie'),
]