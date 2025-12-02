from django.test import TestCase, Client as TestClient
from users.models import CustomUser
from clients.models import Client
from accounts.models import Account
from transactions.models import Transaction
from datetime import date
from decimal import Decimal

class DepositWithdrawalTest(TestCase):
    def setUp(self):
        self.client = TestClient()
        
        # Create a borrower user with client profile
        self.borrower_user = CustomUser.objects.create_user(
            username='borrower',
            email='borrower@example.com',
            password='password123',
            role='borrower'
        )
        
        self.client_profile = Client.objects.create(
            user=self.borrower_user,
            first_name='John',
            last_name='Doe',
            date_of_birth=date(1990, 1, 1),
            address='123 Main St',
            monthly_income=Decimal('1000.00')
        )
        
        # Create an account
        self.account = Account.objects.create(
            client=self.client_profile,
            account_number='1234567890',
            account_type='savings',
            current_balance=Decimal('1000.00'),
            interest_rate=Decimal('2.5'),
            is_active=True
        )

    def test_deposit_success(self):
        self.client.login(username='borrower', password='password123')
        
        response = self.client.post('/transactions/deposit/', {
            'account': self.account.account_id,
            'amount': '500',
            'description': 'Test deposit'
        })
        
        # Should redirect
        self.assertEqual(response.status_code, 302)
        
        # Check balance updated
        self.account.refresh_from_db()
        self.assertEqual(self.account.current_balance, Decimal('1500.00'))
        
        # Check transaction created
        transaction = Transaction.objects.filter(account=self.account, transaction_type='deposit').first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.amount, Decimal('500.00'))

    def test_withdrawal_success(self):
        self.client.login(username='borrower', password='password123')
        
        response = self.client.post('/transactions/withdrawal/', {
            'account': self.account.account_id,
            'amount': '300',
            'description': 'Test withdrawal'
        })
        
        # Should redirect
        self.assertEqual(response.status_code, 302)
        
        # Check balance updated
        self.account.refresh_from_db()
        self.assertEqual(self.account.current_balance, Decimal('700.00'))
        
        # Check transaction created
        transaction = Transaction.objects.filter(account=self.account, transaction_type='withdrawal').first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.amount, Decimal('300.00'))

    def test_withdrawal_insufficient_funds(self):
        self.client.login(username='borrower', password='password123')
        
        response = self.client.post('/transactions/withdrawal/', {
            'account': self.account.account_id,
            'amount': '2000',  # More than balance
            'description': 'Test withdrawal'
        })
        
        # Should not redirect (stays on form)
        self.assertEqual(response.status_code, 200)
        
        # Balance should not change
        self.account.refresh_from_db()
        self.assertEqual(self.account.current_balance, Decimal('1000.00'))

    def test_deposit_negative_amount(self):
        self.client.login(username='borrower', password='password123')
        
        response = self.client.post('/transactions/deposit/', {
            'account': self.account.account_id,
            'amount': '-100',
            'description': 'Test deposit'
        })
        
        # Should not redirect
        self.assertEqual(response.status_code, 200)
        
        # Balance should not change
        self.account.refresh_from_db()
        self.assertEqual(self.account.current_balance, Decimal('1000.00'))

    def test_deposit_get_request(self):
        self.client.login(username='borrower', password='password123')
        
        response = self.client.get('/transactions/deposit/')
        
        # Should show form
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Make Deposit')

    def test_withdrawal_get_request(self):
        self.client.login(username='borrower', password='password123')
        
        response = self.client.get('/transactions/withdrawal/')
        
        # Should show form
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Make Withdrawal')
