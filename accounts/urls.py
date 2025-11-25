from django.urls import path
from . import views

urlpatterns = [
    path('', views.account_list_view, name='account-list'),
    path('create/', views.account_create_view, name='account-create'),
    path('<int:id>/', views.account_detail_view, name='account-detail'),
]
