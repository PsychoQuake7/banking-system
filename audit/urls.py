# audit/urls.py
from django.urls import path
from . import views

app_name = 'audit'

urlpatterns = [
    path('', views.audit_logs_view, name='audit_logs'),
    path('export/csv/', views.export_audit_logs_csv, name='export_csv'),
    path('export/excel/', views.export_audit_logs_excel, name='export_excel'),
]
