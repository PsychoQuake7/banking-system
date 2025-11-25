from django.urls import path
from . import views

urlpatterns = [
    path('', views.notification_list_view, name='notification-list'),
    path('settings/', views.notification_settings_view, name='notification-settings'),
]
