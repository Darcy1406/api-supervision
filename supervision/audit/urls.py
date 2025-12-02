from django.urls import path
from  . import views

urlpatterns = [
    path('get', views.AuditLogView.as_view(), name='get_audit_log'),
]