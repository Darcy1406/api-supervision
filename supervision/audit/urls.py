from django.urls import path
from  . import views

urlpatterns = [
    path('get', views.AuditLogView.as_view(), name='get_audit_log'),
    path('count', views.AuditLogView.as_view(), name='obtenir_nombre_utilisateurs_authentife_par_mois'),
]