from django.test import TestCase, Client as TestClient
from django.contrib.auth import get_user_model
from django.urls import reverse
from clients.models import Client
from loans.models import LoanApplication
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone

User = get_user_model()

class LoanApplicationFilterTests(TestCase):
    def setUp(self):
        # Create staff user
        self.staff_user = User.objects.create_user(
            username='staff1', email='staff@example.com', password='password', role='staff'
        )
        self.staff_user2 = User.objects.create_user(
            username='staff2', email='staff2@example.com', password='password', role='staff'
        )
        
        # Create client
        self.client_user = User.objects.create_user(
            username='client1', email='client@example.com', password='password', role='borrower'
        )
        self.client_obj = Client.objects.create(
            user=self.client_user,
            first_name='Test',
            last_name='Client',
            monthly_income=Decimal('50000.00'),
            credit_score=750,
            date_of_birth='1990-01-01',
            address='123 Test St'
        )
        
        # Create applications
        self.app1 = LoanApplication.objects.create(
            client=self.client_obj,
            loan_amount=Decimal('10000.00'),
            purpose='Test 1',
            status='pending',
            loan_officer=None
        )
        # Manually set application_date to 10 days ago
        self.app1.application_date = timezone.now() - timedelta(days=10)
        self.app1.save()
        
        self.app2 = LoanApplication.objects.create(
            client=self.client_obj,
            loan_amount=Decimal('20000.00'),
            purpose='Test 2',
            status='approved',
            loan_officer=self.staff_user
        )
        self.app2.application_date = timezone.now() - timedelta(days=5)
        self.app2.save()
        
        self.app3 = LoanApplication.objects.create(
            client=self.client_obj,
            loan_amount=Decimal('30000.00'),
            purpose='Test 3',
            status='rejected',
            loan_officer=self.staff_user2
        )
        self.app3.application_date = timezone.now() - timedelta(days=1)
        self.app3.save()
        
        self.client = TestClient()
        self.client.force_login(self.staff_user)
        self.url = reverse('loans:loan_application_list')

    def test_filter_by_status(self):
        response = self.client.get(self.url, {'status': 'approved'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['applications']), 1)
        self.assertEqual(response.context['applications'][0].application_id, self.app2.application_id)
        
        response = self.client.get(self.url, {'status': 'pending'})
        self.assertEqual(len(response.context['applications']), 1)
        self.assertEqual(response.context['applications'][0].application_id, self.app1.application_id)

    def test_filter_by_officer(self):
        response = self.client.get(self.url, {'officer': self.staff_user.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['applications']), 1)
        self.assertEqual(response.context['applications'][0].application_id, self.app2.application_id)
        
        response = self.client.get(self.url, {'officer': self.staff_user2.id})
        self.assertEqual(len(response.context['applications']), 1)
        self.assertEqual(response.context['applications'][0].application_id, self.app3.application_id)

    def test_filter_by_date_range(self):
        start_date = (timezone.now() - timedelta(days=7)).date()
        end_date = (timezone.now() - timedelta(days=3)).date()
        
        response = self.client.get(self.url, {
            'start_date': start_date,
            'end_date': end_date
        })
        self.assertEqual(response.status_code, 200)
        # Should match app2 (5 days ago)
        self.assertEqual(len(response.context['applications']), 1)
        self.assertEqual(response.context['applications'][0].application_id, self.app2.application_id)

    def test_combined_filters(self):
        # Status approved AND officer staff1
        response = self.client.get(self.url, {
            'status': 'approved',
            'officer': self.staff_user.id
        })
        self.assertEqual(len(response.context['applications']), 1)
        self.assertEqual(response.context['applications'][0].application_id, self.app2.application_id)
        
        # Status rejected AND officer staff1 (should be empty)
        response = self.client.get(self.url, {
            'status': 'rejected',
            'officer': self.staff_user.id
        })
        self.assertEqual(len(response.context['applications']), 0)
