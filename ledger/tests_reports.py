from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone
from decimal import Decimal
from ledger.models import GLAccount, LedgerEntry
from ledger.services import FinancialReportService
from transactions.models import Transaction
from accounts.models import Account
from clients.models import Client
from django.contrib.auth import get_user_model

User = get_user_model()

class FinancialReportTests(TestCase):
    def setUp(self):
        # Initialize GL Accounts
        call_command('init_ledger', stdout=None)
        
        # Setup basic data
        self.user = User.objects.create_user(
            username='testuser', 
            password='password',
            email='test@example.com'
        )
        self.client = Client.objects.create(
            user=self.user, 
            first_name='Test', 
            last_name='User',
            date_of_birth='1990-01-01',
            address='123 Test St'
        )
        self.account = Account.objects.create(
            client=self.client,
            account_type='savings',
            account_number='1234567890'
        )
        
        # Create some ledger entries manually to simulate financial activity
        self.cash_vault = GLAccount.objects.get(code='1001')
        self.interest_income = GLAccount.objects.get(code='4001') # Revenue
        self.client_deposits = GLAccount.objects.get(code='2001')
        
        # Simulate Interest Income (Revenue)
        # Debit Cash Vault (Asset Increase), Credit Interest Income (Revenue Increase)
        LedgerEntry.objects.create(
            gl_account=self.cash_vault,
            amount=Decimal('500.00'),
            debit_credit='debit',
            description='Interest Payment Received'
        )
        LedgerEntry.objects.create(
            gl_account=self.interest_income,
            amount=Decimal('500.00'),
            debit_credit='credit',
            description='Interest Income'
        )

    def test_income_statement_calculation(self):
        report = FinancialReportService.get_income_statement()
        
        self.assertEqual(report['total_revenue'], Decimal('500.00'))
        self.assertEqual(report['total_expenses'], Decimal('0.00'))
        self.assertEqual(report['net_income'], Decimal('500.00'))
        
        # Verify revenue detail
        self.assertEqual(len(report['revenues']), 1)
        self.assertEqual(report['revenues'][0]['code'], '4001')
        self.assertEqual(report['revenues'][0]['balance'], Decimal('500.00'))

    def test_date_filtering(self):
        # Create an old entry
        old_date = timezone.now() - timezone.timedelta(days=365)
        
        entry1 = LedgerEntry.objects.create(
            gl_account=self.interest_income,
            amount=Decimal('100.00'),
            debit_credit='credit',
            description='Old Income'
        )
        entry1.created_at = old_date
        entry1.save()
        
        # Test filtering
        today = timezone.now().date()
        report = FinancialReportService.get_income_statement(start_date=today)
        
        # Should only include the 500.00 from setUp, not the 100.00 from last year
        self.assertEqual(report['total_revenue'], Decimal('500.00'))
