from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from clients.models import Client as ClientModel
from utils.excel_generator import generate_financial_report_excel, generate_loan_report_excel
from decimal import Decimal
import openpyxl
from io import BytesIO

User = get_user_model()

class ExcelExportTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='staffuser', 
            password='password',
            email='staff@example.com',
            role='staff',
            is_staff=True
        )
        self.client_profile = ClientModel.objects.create(
            user=self.user,
            first_name='Staff',
            last_name='User',
            date_of_birth='1990-01-01',
            address='123 Staff St'
        )

    def test_financial_excel_generator(self):
        """Test the generator function directly"""
        report_data = {
            'revenues': [{'name': 'Interest Income', 'code': '4001', 'balance': Decimal('1000.00')}],
            'expenses': [],
            'total_revenue': Decimal('1000.00'),
            'total_expenses': Decimal('0.00'),
            'net_income': Decimal('1000.00')
        }
        response = generate_financial_report_excel(report_data, None, None)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
        # Verify Excel content
        wb = openpyxl.load_workbook(BytesIO(response.content))
        ws = wb.active
        self.assertEqual(ws.title, "Income Statement")
        self.assertEqual(ws['A1'].value, "Kayamanan Banking System - Income Statement")

    def test_financial_report_view_excel(self):
        self.client.login(username='staffuser', password='password')
        url = reverse('ledger:financial_report')
        
        # Excel request
        response = self.client.get(url, {'export': 'excel'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertIn('financial_report.xlsx', response['Content-Disposition'])

    def test_loan_reports_view_excel(self):
        self.client.login(username='staffuser', password='password')
        url = reverse('loans:loan_reports')
        
        # Excel request
        response = self.client.get(url, {'export': 'excel'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertIn('loan_reports.xlsx', response['Content-Disposition'])
