from django.urls import path
from  . import views

from django.urls import path
from . import views

urlpatterns = [
    path("login", views.LoginView.as_view(), name="api-login"),
    path("logout", views.LogoutView.as_view(), name="api-logout"),
    path("get_user", views.UserView.as_view(), name="api-user"),
    path("csrf", views.GetCSRFToken.as_view(), name="api-csrf"),

    path("poste_comptable/get", views.PosteComptableView.as_view(), name="api-poste-comptable-get"),
    path("poste_comptable/all", views.PosteComptableView.as_view(), name="liste-de-tous-les-poste-comptables"),
]
