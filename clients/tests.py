from django.test import TestCase, Client as TestClient
from django.contrib.auth import get_user_model
from django.urls import reverse
from datetime import date
from decimal import Decimal
from .models import Client

class ClientAccessTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        
        # Create users
        self.admin_user = self.User.objects.create_superuser('admin', 'admin@example.com', 'password', role='admin')
        self.staff_user = self.User.objects.create_user('staff', 'staff@example.com', 'password', role='staff')
        self.borrower_user = self.User.objects.create_user('borrower', 'borrower@example.com', 'password', role='borrower')
        
        # Create client for borrower
        self.client_model = Client.objects.create(
            user=self.borrower_user,
            first_name='Original',
            last_name='Name',
            date_of_birth=date(1990, 1, 1),
            address='Original Address',
            monthly_income=Decimal('50000.00'),
            credit_score=700
        )
        
        self.client_edit_url = reverse('clients:client_edit', args=[self.client_model.client_id])
        self.toggle_status_url = reverse('clients:toggle_status', args=[self.client_model.client_id])

    def test_admin_can_access_edit_view(self):
        self.client.login(username='admin', password='password')
        response = self.client.get(self.client_edit_url)
        self.assertEqual(response.status_code, 200)
        
    def test_staff_cannot_access_edit_view(self):
        self.client.login(username='staff', password='password')
        response = self.client.get(self.client_edit_url)
        self.assertEqual(response.status_code, 403)
        
    def test_borrower_cannot_access_edit_view(self):
        self.client.login(username='borrower', password='password')
        response = self.client.get(self.client_edit_url)
        self.assertEqual(response.status_code, 403)

    def test_admin_can_update_client(self):
        self.client.login(username='admin', password='password')
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'borrower@example.com',
            'phone': '1234567890',
            'date_of_birth': '1990-01-01',
            'address': 'Updated Address',
            'monthly_income': '60000',
            'credit_score': '750',
            'is_active': 'on'
        }
        response = self.client.post(self.client_edit_url, data)
        self.assertEqual(response.status_code, 302) # Redirects on success
        
        self.client_model.refresh_from_db()
        updated_client = Client.objects.get(pk=self.client_model.pk)
        self.assertEqual(updated_client.first_name, 'Updated')
        self.assertEqual(updated_client.address, 'Updated Address')
        self.assertEqual(updated_client.user.phone, '1234567890')

    def test_admin_can_toggle_status(self):
        self.client.login(username='admin', password='password')
        
        # Deactivate
        response = self.client.get(self.toggle_status_url)
        self.assertEqual(response.status_code, 302)
        self.borrower_user.refresh_from_db()
        self.assertFalse(self.borrower_user.is_active)
        
        # Activate
        response = self.client.get(self.toggle_status_url)
        self.assertEqual(response.status_code, 302)
        self.borrower_user.refresh_from_db()
        self.assertTrue(self.borrower_user.is_active)

    def test_staff_cannot_toggle_status(self):
        self.client.login(username='staff', password='password')
        response = self.client.get(self.toggle_status_url)
        self.assertEqual(response.status_code, 403)
