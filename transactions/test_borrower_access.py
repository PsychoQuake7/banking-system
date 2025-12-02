from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from users.models import CustomUser
from clients.models import Client
from transactions.views import transaction_list_view
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import PermissionDenied
from datetime import date

class BorrowerAccessTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        
        # Create a borrower user
        self.borrower_user = CustomUser.objects.create_user(
            username='borrower',
            email='borrower@example.com',
            password='password123',
            role='borrower'
        )
        
        # Create a borrower user WITHOUT client profile
        self.borrower_no_client = CustomUser.objects.create_user(
            username='borrower_no_client',
            email='noclient@example.com',
            password='password123',
            role='borrower'
        )

    def test_borrower_with_client_access(self):
        # Create client profile for the first borrower
        Client.objects.create(
            user=self.borrower_user,
            first_name='John',
            last_name='Doe',
            date_of_birth=date(1990, 1, 1),
            address='123 Main St',
            monthly_income=1000.00
        )
        
        request = self.factory.get('/transactions/')
        request.user = self.borrower_user
        
        # Setup messages
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        response = transaction_list_view(request)
        self.assertEqual(response.status_code, 200)

    def test_borrower_without_client_access(self):
        # This user has no client profile
        request = self.factory.get('/transactions/')
        request.user = self.borrower_no_client
        
        # Setup messages
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        response = transaction_list_view(request)
        
        # Should return 200 OK (not 403)
        self.assertEqual(response.status_code, 200)
        
        # Check for warning message
        messages_list = list(messages)
        self.assertTrue(any("client profile is not set up" in str(m) for m in messages_list))

    def test_borrower_transfer_access(self):
        from transactions.views import transfer_create_view
        
        request = self.factory.get('/transactions/transfer/')
        request.user = self.borrower_user
        
        # Setup messages
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        response = transfer_create_view(request)
        self.assertEqual(response.status_code, 200)

    def test_staff_access(self):
        staff_user = CustomUser.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='password123',
            role='staff'
        )
        request = self.factory.get('/transactions/')
        request.user = staff_user
        
        response = transaction_list_view(request)
        self.assertEqual(response.status_code, 200)
