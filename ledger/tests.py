from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth import get_user_model
from clients.models import Client
from accounts.models import Account
from transactions.models import Transaction
from ledger.models import LedgerEntry, GLAccount
from decimal import Decimal

User = get_user_model()

class LedgerTests(TestCase):
    def setUp(self):
        # Initialize GL Accounts
        call_command('init_ledger', stdout=None)
        
        # Create User and Client
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpassword',
            email='test@example.com',
            role='borrower'
        )
        self.client = Client.objects.create(
            user=self.user,
            first_name='Test',
            last_name='User',
            date_of_birth='1990-01-01',
            address='123 Test St',
            monthly_income=50000
        )
        self.account = Account.objects.create(
            client=self.client,
            account_type='savings',
            account_number='1234567890',
            current_balance=Decimal('0.00')
        )

    def test_deposit_creates_ledger_entries(self):
        # Perform Deposit
        self.account.deposit(Decimal('1000.00'))
        
        # Check Ledger Entries
        entries = LedgerEntry.objects.filter(transaction_ref__account=self.account)
        self.assertEqual(entries.count(), 2)
        
        debit_entry = entries.get(debit_credit='debit')
        credit_entry = entries.get(debit_credit='credit')
        
        # Debit Cash Vault (Asset)
        self.assertEqual(debit_entry.gl_account.code, '1001')
        self.assertEqual(debit_entry.amount, Decimal('1000.00'))
        
        # Credit Client Deposits (Liability)
        self.assertEqual(credit_entry.gl_account.code, '2001')
        self.assertEqual(credit_entry.amount, Decimal('1000.00'))

    def test_withdrawal_creates_ledger_entries(self):
        self.account.deposit(Decimal('1000.00'))
        self.account.withdraw(Decimal('500.00'))
        
        # Get latest transaction (withdrawal)
        transaction = Transaction.objects.last()
        entries = LedgerEntry.objects.filter(transaction_ref=transaction)
        
        self.assertEqual(entries.count(), 2)
        
        debit_entry = entries.get(debit_credit='debit')
        credit_entry = entries.get(debit_credit='credit')
        
        # Debit Client Deposits (Liability Decrease)
        self.assertEqual(debit_entry.gl_account.code, '2001')
        
        # Credit Cash Vault (Asset Decrease)
        self.assertEqual(credit_entry.gl_account.code, '1001')

    def test_ledger_balance(self):
        self.account.deposit(Decimal('1000.00'))
        self.account.withdraw(Decimal('200.00'))
        
        total_debits = sum(e.amount for e in LedgerEntry.objects.filter(debit_credit='debit'))
        total_credits = sum(e.amount for e in LedgerEntry.objects.filter(debit_credit='credit'))
        
        self.assertEqual(total_debits, total_credits)
