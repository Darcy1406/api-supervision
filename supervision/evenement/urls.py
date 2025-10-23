from django.urls import path
from  . import views

urlpatterns = [
    path('', views.index, name='liste_agenda'),
    path("csrf", views.get_csrf, name="get-csrf"),
    path('create', views.create, name='ajout_agenda'),
    path('get', views.read, name='lire_agenda'),
   

]