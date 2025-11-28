from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('', views.client_list_view, name='client_list'),
    path('<int:id>/', views.client_detail_view, name='client_detail'),
    path('<int:id>/edit/', views.client_edit_view, name='client_edit'),
    path('toggle-status/<int:id>/', views.toggle_user_status, name='toggle_status'),
]
