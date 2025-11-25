from django.urls import path
from . import views

urlpatterns = [
    path('', views.loan_list_view, name='loan-list'),
    path('<int:id>/', views.loan_detail_view, name='loan-detail'),
    path('application/', views.loan_application_view, name='loan-application'),
    path('applications/', views.loan_application_list_view, name='loan-application-list'),
    path('<int:id>/payment/', views.make_payment_view, name='make-payment'),
    path('<int:id>/amortization/', views.amortization_schedule_view, name='amortization-schedule'),
]
