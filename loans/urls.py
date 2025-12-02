from django.urls import path
from . import views
from . import views_reports

app_name = 'loans'

urlpatterns = [
    path('', views.loan_list_view, name='loan_list'),
    path('<int:id>/', views.loan_detail_view, name='loan_detail'),
    path('application/', views.loan_application_view, name='loan_application'),
    path('eligibility/', views.loan_eligibility_check_view, name='loan_eligibility_check'),
    path('applications/', views.loan_application_list_view, name='loan_application_list'),
    path('application/<int:id>/', views.loan_application_detail_view, name='loan_application_detail'),
    path('application/<int:id>/approve/', views.approve_loan_application_view, name='approve_loan_application'),
    path('application/<int:id>/reject/', views.reject_loan_application_view, name='reject_loan_application'),
    path('reports/', views_reports.loan_reports_view, name='loan_reports'),
    path('reports/delinquent/', views_reports.delinquent_accounts_view, name='delinquent_accounts'),
    path('reports/repayments/', views_reports.repayment_reports_view, name='repayment_reports'),
    path('<int:id>/payment/', views.make_payment_view, name='make_payment'),
    path('<int:id>/disburse/', views.disburse_loan_view, name='disburse_loan'),
    path('<int:id>/amortization/', views.amortization_schedule_view, name='amortization_schedule'),
    path('<int:loan_id>/agreement/download/', views.download_loan_agreement_view, name='download_loan_agreement'),
]
