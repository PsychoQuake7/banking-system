from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('', views.transaction_list_view, name='transaction_list'),  # Changed to underscore
    path('create/', views.transaction_create_view, name='transaction_create'),  # Changed to underscore
    path('transfer/', views.transfer_create_view, name='transfer_create'),  # Changed to underscore
]