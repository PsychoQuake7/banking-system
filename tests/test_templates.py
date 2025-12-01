from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from clients.models import Client as ClientModel
from accounts.models import Account
from loans.models import LoanApplication
from datetime import date

User = get_user_model()

class TemplateRenderingTest(TestCase):
    def setUp(self):
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password123',
            role='admin'
        )
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='password123',
            role='staff'
        )
        
        # Create client user and profile
        self.client_user = User.objects.create_user(
            username='client',
            email='client@example.com',
            password='password123',
            role='borrower'
        )
        self.client_profile = ClientModel.objects.create(
            user=self.client_user,
            first_name='John',
            last_name='Doe',
            date_of_birth=date(1990, 1, 1),
            address='123 Main St',
            monthly_income=50000,
            credit_score=750
        )
        
        self.client = Client()

    def test_client_list_rendering(self):
        self.client.force_login(self.staff_user)
        response = self.client.get('/clients/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'clients/client_list.html')

    def test_client_detail_rendering_no_credit_score(self):
        # Create client with no credit score (if possible, or 0)
        client_no_score = ClientModel.objects.create(
            user=User.objects.create_user(username='client2', email='client2@example.com', role='borrower'),
            first_name='Jane',
            last_name='Doe',
            date_of_birth=date(1990, 1, 1),
            address='123 Main St',
            monthly_income=50000,
            credit_score=0 # Simulating low/no score
        )
        self.client.force_login(self.staff_user)
        response = self.client.get(f'/clients/{client_no_score.client_id}/')
        self.assertEqual(response.status_code, 200)

    def test_loan_application_list_rendering_with_officers(self):
        # Ensure loan officers exist to trigger the loop in template
        self.client.force_login(self.staff_user)
        try:
            response = self.client.get('/loans/applications/')
            self.assertEqual(response.status_code, 200)
            # Check if staff user is in the context as officer
            self.assertContains(response, self.staff_user.username)
        except Exception as e:
            print(f"Error during rendering: {e}")
            raise
