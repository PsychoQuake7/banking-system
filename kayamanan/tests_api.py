from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from clients.models import Client as ClientModel
from accounts.models import Account
from loans.models import Loan, LoanApplication
from transactions.models import Transaction
from decimal import Decimal

User = get_user_model()

class DashboardAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpassword', 
            email='test@example.com', 
            role='borrower'
        )
        self.client_profile = ClientModel.objects.create(
            user=self.user,
            first_name='Test',
            last_name='User',
            date_of_birth='1990-01-01',
            address='123 Test St',
            monthly_income=50000
        )
        self.account = Account.objects.create(
            client=self.client_profile,
            account_type='savings',
            account_number='1234567890',
            current_balance=Decimal('1000.00')
        )

    def test_api_requires_login(self):
        response = self.client.get(reverse('dashboard_data_api'))
        self.assertEqual(response.status_code, 302)  # Should redirect to login

    def test_api_returns_correct_data(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('dashboard_data_api'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['total_balance'], 1000.0)
        self.assertEqual(data['accounts_count'], 1)
        self.assertEqual(data['active_loans_count'], 0)
        self.assertIn('last_updated', data)

    def test_api_reflects_changes(self):
        self.client.login(username='testuser', password='testpassword')
        
        # Initial check
        response = self.client.get(reverse('dashboard_data_api'))
        self.assertEqual(response.json()['total_balance'], 1000.0)
        
        # Update balance
        self.account.current_balance = Decimal('2000.00')
        self.account.save()
        
        # Check again
        response = self.client.get(reverse('dashboard_data_api'))
        self.assertEqual(response.json()['total_balance'], 2000.0)

    def test_api_transactions(self):
        self.client.login(username='testuser', password='testpassword')
        
        # Create transaction
        Transaction.objects.create(
            account=self.account,
            transaction_type='deposit',
            amount=Decimal('500.00'),
            description='Test Deposit'
        )
        
        response = self.client.get(reverse('dashboard_data_api'))
        data = response.json()
        
        self.assertEqual(len(data['recent_transactions']), 1)
        self.assertEqual(data['recent_transactions'][0]['amount'], 500.0)
        self.assertEqual(data['recent_transactions'][0]['type'], 'deposit')
