from django.test import TestCase, Client as TestClient
from users.models import CustomUser
from clients.models import Client
from accounts.models import Account
from datetime import date
from decimal import Decimal

class AccountCreationTest(TestCase):
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

    def test_create_savings_account(self):
        self.client.login(username='borrower', password='password123')
        
        response = self.client.post('/accounts/create/', {
            'account_type': 'savings',
            'initial_deposit': '1000',
            'terms': 'on'
        })
        
        # Should redirect to account detail
        self.assertEqual(response.status_code, 302)
        
        # Check account was created
        account = Account.objects.filter(client=self.client_profile).first()
        self.assertIsNotNone(account)
        self.assertEqual(account.account_type, 'savings')
        self.assertEqual(account.current_balance, Decimal('1000.00'))
        self.assertEqual(account.interest_rate, Decimal('2.5'))

    def test_create_checking_account(self):
        self.client.login(username='borrower', password='password123')
        
        response = self.client.post('/accounts/create/', {
            'account_type': 'checking',
            'initial_deposit': '1500',
            'terms': 'on'
        })
        
        self.assertEqual(response.status_code, 302)
        
        account = Account.objects.filter(client=self.client_profile, account_type='checking').first()
        self.assertIsNotNone(account)
        self.assertEqual(account.interest_rate, Decimal('0.0'))

    def test_minimum_deposit_validation(self):
        self.client.login(username='borrower', password='password123')
        
        response = self.client.post('/accounts/create/', {
            'account_type': 'savings',
            'initial_deposit': '400',
            'terms': 'on'
        })
        
        # Should not redirect (stays on form)
        self.assertEqual(response.status_code, 200)
        
        # No account should be created
        self.assertEqual(Account.objects.filter(client=self.client_profile).count(), 0)

    def test_terms_required(self):
        self.client.login(username='borrower', password='password123')
        
        response = self.client.post('/accounts/create/', {
            'account_type': 'savings',
            'initial_deposit': '1000'
            # No 'terms' field
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Account.objects.filter(client=self.client_profile).count(), 0)
