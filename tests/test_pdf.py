from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from clients.models import Client as ClientModel
from utils.pdf_generator import generate_financial_report_pdf, generate_loan_report_pdf
from decimal import Decimal

User = get_user_model()

class PDFExportTests(TestCase):
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

    def test_financial_pdf_generator(self):
        """Test the generator function directly"""
        report_data = {
            'revenues': [{'name': 'Interest Income', 'code': '4001', 'balance': Decimal('1000.00')}],
            'expenses': [],
            'total_revenue': Decimal('1000.00'),
            'total_expenses': Decimal('0.00'),
            'net_income': Decimal('1000.00')
        }
        response = generate_financial_report_pdf(report_data, None, None)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_financial_report_view_pdf(self):
        self.client.login(username='staffuser', password='password')
        url = reverse('ledger:financial_report')
        
        # PDF request
        response = self.client.get(url, {'export': 'pdf'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('financial_report.pdf', response['Content-Disposition'])

    def test_loan_reports_view_pdf(self):
        self.client.login(username='staffuser', password='password')
        url = reverse('loans:loan_reports')
        
        # PDF request
        response = self.client.get(url, {'export': 'pdf'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('loan_reports.pdf', response['Content-Disposition'])
