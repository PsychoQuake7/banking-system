from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from ledger.models import GLAccount, LedgerEntry
from ledger.services import FinancialReportService

User = get_user_model()

class AccountingFeaturesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='staffuser', 
            password='password',
            email='staff@example.com',
            role='staff',
            is_staff=True
        )
        self.client = Client()
        
        # Create GL Accounts
        self.asset = GLAccount.objects.create(name='Cash', code='1001', account_type='asset')
        self.liability = GLAccount.objects.create(name='Deposits', code='2001', account_type='liability')
        self.equity = GLAccount.objects.create(name='Capital', code='3001', account_type='equity')
        self.revenue = GLAccount.objects.create(name='Sales', code='4001', account_type='revenue')
        self.expense = GLAccount.objects.create(name='Rent', code='5001', account_type='expense')
        
        # Create entries to form a balanced scenario
        # 1. Initial Capital: Dr Cash 1000, Cr Capital 1000
        LedgerEntry.objects.create(gl_account=self.asset, amount=1000, debit_credit='debit', description='Init')
        LedgerEntry.objects.create(gl_account=self.equity, amount=1000, debit_credit='credit', description='Init')
        
        # 2. Revenue: Dr Cash 500, Cr Sales 500
        LedgerEntry.objects.create(gl_account=self.asset, amount=500, debit_credit='debit', description='Rev')
        LedgerEntry.objects.create(gl_account=self.revenue, amount=500, debit_credit='credit', description='Rev')
        
        # 3. Expense: Dr Rent 200, Cr Cash 200
        LedgerEntry.objects.create(gl_account=self.expense, amount=200, debit_credit='debit', description='Exp')
        LedgerEntry.objects.create(gl_account=self.asset, amount=200, debit_credit='credit', description='Exp')

    def test_balance_sheet_equation(self):
        """
        Verify Assets = Liabilities + Equity (including Current Year Earnings)
        """
        report = FinancialReportService.get_balance_sheet()
        
        # Calculations:
        # Cash: 1000 + 500 - 200 = 1300 (Asset)
        # Capital: 1000 (Equity)
        # Sales: 500 (Revenue)
        # Rent: 200 (Expense)
        # Current Earnings: 500 - 200 = 300
        # Total Equity: 1000 + 300 = 1300
        
        self.assertEqual(report['total_assets'], Decimal('1300.00'))
        self.assertEqual(report['total_liabilities'], Decimal('0.00'))
        self.assertEqual(report['total_equity'], Decimal('1300.00'))
        self.assertEqual(report['total_assets'], report['total_liabilities_equity'])

    def test_balance_sheet_view(self):
        self.client.login(username='staffuser', password='password')
        url = reverse('ledger:balance_sheet')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Balance Sheet')
        self.assertContains(response, 'Total Assets')

    def test_general_ledger_view(self):
        self.client.login(username='staffuser', password='password')
        url = reverse('ledger:general_ledger')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cash')
        self.assertContains(response, '1001')

    def test_gl_account_detail_view(self):
        self.client.login(username='staffuser', password='password')
        url = reverse('ledger:gl_account_detail', args=['1001'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Init')
        self.assertContains(response, 'Rev')
