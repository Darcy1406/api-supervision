from django.urls import path
from  . import views

urlpatterns = [
    path('', views.index, name='index'),

    path('piece/create', views.PieceView.as_view(), name='create_piece'),
    path('piece/get_pieces', views.PieceView.as_view(), name='get_pieces'),
    path('piece/update', views.PieceView.as_view(), name='update_piece'),

    path('document/save', views.DocumentView.as_view(), name='save_document'),
    path('document/liste', views.DocumentView.as_view(), name='liste_document'),
    path('document/rechercher', views.DocumentView.as_view(), name='rechercher_un_document'),

    path('transcription/create', views.TranscriptionView.as_view(), name='create_transcription'),
    path('transcription/liste', views.TranscriptionView.as_view(), name='liste_transcription'),

    path('compte/get_number', views.CompteView.as_view(), name='get_number_compte'),

    path('piece_compte/creer', views.PieceCompteView.as_view(), name='creer_liaison_piece_compte'),
    path('piece_compte/modifier', views.PieceCompteView.as_view(), name='modifier_liaison_piece_compte'),
    path('piece_compte/lister', views.PieceCompteView.as_view(), name='lister_liaison_piece_compte'),
    path('piece_compte/liste_liaison_pour_une_piece', views.PieceCompteView.as_view(), name='liste_liaison_pour_une_piece'),
    
    # path('compte/create', views.CompteView.as_view(), name='get_comptes'),
    # path('compte/get_comptes', views.CompteView.as_view(), name='get_comptes'),
    # path('compte/get_comptes_regroupements', views.CompteView.as_view(), name='get_comptes'),
]