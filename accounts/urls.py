from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.account_list_view, name='account_list'),
    path('create/', views.account_create_view, name='account_create'),
    path('<int:id>/', views.account_detail_view, name='account_sdetail'),
]
