from django.urls import path
from  . import views

from django.urls import path
from . import views

urlpatterns = [
    
    path("login", views.LoginView.as_view(), name="api-login"),
    path("logout", views.LogoutView.as_view(), name="api-logout"),
    path("get_user", views.UserView.as_view(), name="api-user"),
    path("get_auditeurs_zone", views.UserView.as_view(), name="recuperer_auditeurs_zone"),
    path("csrf", views.GetCSRFToken.as_view(), name="api-csrf"),
    path("zone/get", views.ZoneView.as_view(), name="recuper_tous_les_zones"),

    path("poste_comptable/get", views.PosteComptableView.as_view(), name="api-poste-comptable-get"),
    path("poste_comptable/all", views.PosteComptableView.as_view(), name="liste-des-poste-comptables"),
    path("poste_comptable/type", views.PosteComptableView.as_view(), name="liste-de-tous-les-types-postes-comptables"),
    path("poste_comptable/selectionner_poste_piece", views.PosteComptableView.as_view(), name="selectionner-tous-les-postes-lies-au-piece"),
]
