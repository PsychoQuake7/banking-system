from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list_view, name='notification_list'),
    path('send/', views.send_notification_view, name='send_notification'),
    path('settings/', views.notification_settings_view, name='notification_settings'),
]
