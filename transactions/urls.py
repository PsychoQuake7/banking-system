from django.urls import path
from . import views

urlpatterns = [
    path('', views.transaction_list_view, name='transaction-list'),
    path('create/', views.transaction_create_view, name='transaction-create'),
    path('transfer/', views.transfer_create_view, name='transfer-create'),
]
