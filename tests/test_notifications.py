from django.test import TestCase
from django.core import mail
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from notifications.services import NotificationService
from notifications.models import Notification
from loans.models import Loan, LoanApplication
from clients.models import Client
from django.core.management import call_command
from io import StringIO

User = get_user_model()

class NotificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testclient',
            email='client@example.com',
            password='password'
        )
        self.client_profile = Client.objects.create(
            user=self.user,
            first_name='Test',
            last_name='Client',
            date_of_birth='1990-01-01',
            address='123 Test St'
        )

    def test_notification_service(self):
        """Test that service sends email and creates record"""
        NotificationService.send_notification(
            user=self.user,
            subject="Test Subject",
            message="Test Message",
            notification_type='system_alert',
            related_entity_type='system',
            related_entity_id=0
        )
        
        # Check Email
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Test Subject")
        
        # Check Database
        self.assertEqual(Notification.objects.count(), 2) # 1 Email, 1 SMS
        email_notif = Notification.objects.get(type='email')
        self.assertEqual(email_notif.subject, "Test Subject")
        self.assertEqual(email_notif.status, 'sent')

    def test_reminder_command(self):
        """Test that command sends reminder for due loan"""
        # Create loan due in 3 days
        app = LoanApplication.objects.create(
            client=self.client_profile,
            loan_amount=10000,
            term_months=12,
            purpose='Test',
            status='approved'
        )
        loan = Loan.objects.create(
            application=app,
            loan_amount=10000,
            interest_rate=5,
            term_months=12,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=365),
            remaining_balance=10000,
            status='active'
        )
        
        from loans.models import AmortizationSchedule
        AmortizationSchedule.objects.create(
            loan=loan,
            installment_number=1,
            due_date=timezone.now().date() + timedelta(days=3),
            principal_amount=1000,
            interest_amount=100,
            total_payment=1100,
            status='pending'
        )
        
        out = StringIO()
        call_command('send_due_date_reminders', stdout=out)
        
        self.assertIn("Sent 1 reminders", out.getvalue())
        
        # Verify notification created
        self.assertTrue(Notification.objects.filter(
            user=self.user,
            notification_type='payment_reminder',
            related_entity_id=loan.loan_id
        ).exists())
