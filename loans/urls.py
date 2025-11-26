from django.urls import path
from . import views

app_name = 'loans'

urlpatterns = [
    path('', views.loan_list_view, name='loan_list'),
    path('<int:id>/', views.loan_detail_view, name='loan_detail'),
    path('application/', views.loan_application_view, name='loan_application'),
    path('applications/', views.loan_application_list_view, name='loan_application_list'),
    path('<int:id>/payment/', views.make_payment_view, name='make_payment'),
    path('<int:id>/amortization/', views.amortization_schedule_view, name='amortization_schedule'),
]
