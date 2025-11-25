from django.urls import path
from . import views

urlpatterns = [
    path('', views.client_list_view, name='client-list'),
    path('<int:id>/', views.client_detail_view, name='client-detail'),
    path('<int:id>/edit/', views.client_edit_view, name='client-edit'),
]
