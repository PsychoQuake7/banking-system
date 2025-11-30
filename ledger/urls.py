from django.urls import path
from . import views

app_name = 'ledger'

urlpatterns = [
    path('reports/financial/', views.financial_report_view, name='financial_report'),
    path('reports/balance-sheet/', views.balance_sheet_view, name='balance_sheet'),
    path('general-ledger/', views.general_ledger_view, name='general_ledger'),
    path('general-ledger/<str:code>/', views.gl_account_detail_view, name='gl_account_detail'),
]
