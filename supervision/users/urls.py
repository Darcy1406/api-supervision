from django.urls import path
from  . import views

urlpatterns = [
    path('login', views.authentification, name='authentification'),
    path("csrf", views.get_csrf, name="get-csrf"),

]