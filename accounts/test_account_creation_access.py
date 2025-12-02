from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from users.models import CustomUser
from clients.models import Client
from accounts.views import account_create_view
from django.contrib.messages.storage.fallback import FallbackStorage
from datetime import date

class AccountCreationAccessTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        
        # Create a borrower user
        self.borrower_user = CustomUser.objects.create_user(
            username='borrower',
            email='borrower@example.com',
            password='password123',
            role='borrower'
        )
        
        # Create client profile for the borrower
        Client.objects.create(
            user=self.borrower_user,
            first_name='John',
            last_name='Doe',
            date_of_birth=date(1990, 1, 1),
            address='123 Main St',
            monthly_income=1000.00
        )

    def test_borrower_access(self):
        request = self.factory.get('/accounts/create/')
        request.user = self.borrower_user
        
        # Setup messages
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        response = account_create_view(request)
        self.assertEqual(response.status_code, 200)

    def test_staff_access(self):
        staff_user = CustomUser.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='password123',
            role='staff'
        )
        request = self.factory.get('/accounts/create/')
        request.user = staff_user
        
        response = account_create_view(request)
        self.assertEqual(response.status_code, 200)
