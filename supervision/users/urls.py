from django.urls import path
from  . import views

from django.urls import path

urlpatterns = [
    
    path("login", views.LoginView.as_view(), name="api-login"),
    path("logout", views.LogoutView.as_view(), name="api-logout"),

    path("get_user", views.UserView.as_view(), name="api-user"),
    path('create_user', views.UserView.as_view(), name='create_user'),
    path('update_user', views.UserView.as_view(), name='update_user'),
    path('liste', views.UserView.as_view(), name='liste_de_tous_les_utilisateurs_du_systeme'),
    path('delete',views.UserView.as_view(), name='supprimer_un_utilisateur'),
    path('create_authentification', views.UserView.as_view(), name='creer_une_authentification_pour_un_utilisateur'),

    path("get_auditeurs_zone", views.UserView.as_view(), name="recuperer_auditeurs_zone"),
    path("get_auditeurs", views.UserView.as_view(), name="recuperer_auditeurs"),
    path("csrf", views.GetCSRFToken.as_view(), name="api-csrf"),

    path("zone/get", views.ZoneView.as_view(), name="recuper_tous_les_zones"),

    path("poste_comptable/create", views.PosteComptableView.as_view(), name="creer_un_poste_comptable"),
    path("poste_comptable/update", views.PosteComptableView.as_view(), name="modifier_un_poste_comptable"),
    path("poste_comptable/delete", views.PosteComptableView.as_view(), name="supprimer_un_poste_comptable"),
    path("poste_comptable/get", views.PosteComptableView.as_view(), name="api-poste-comptable-get"),
    path("poste_comptable/all", views.PosteComptableView.as_view(), name="liste-des-poste-comptables"),
    path("poste_comptable/type", views.PosteComptableView.as_view(), name="liste-de-tous-les-types-postes-comptables"),
    path("poste_comptable/selectionner_poste_piece", views.PosteComptableView.as_view(), name="selectionner-tous-les-postes-lies-au-piece"),
]
