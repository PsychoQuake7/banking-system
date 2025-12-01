from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.admin_create_user, name='admin_create_user'),
]
