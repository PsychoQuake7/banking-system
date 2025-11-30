from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
from clients.models import Client
from accounts.models import Account
from loans.models import Loan, LoanApplication, AmortizationSchedule
from loans.reports import LoanReportService
from transactions.models import Transaction

User = get_user_model()

class LoanReportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            password='password',
            email='test@example.com'
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
            account_number='1234567890'
        )
        
        # Create Loan Application
        self.application = LoanApplication.objects.create(
            client=self.client,
            loan_amount=Decimal('10000.00'),
            term_months=12,
            purpose='Test Loan',
            status='approved'
        )
        
        # Create Active Loan
        self.loan = Loan.objects.create(
            application=self.application,
            loan_amount=Decimal('10000.00'),
            interest_rate=Decimal('0.10'),
            term_months=12,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=365),
            remaining_balance=Decimal('10000.00'),
            status='active'
        )

    def test_get_active_loans(self):
        active_loans = LoanReportService.get_active_loans()
        self.assertEqual(active_loans.count(), 1)
        self.assertEqual(active_loans.first(), self.loan)
        
        # Test non-active
        self.loan.status = 'paid'
        self.loan.save()
        self.assertEqual(LoanReportService.get_active_loans().count(), 0)

    def test_get_delinquent_loans(self):
        # Create an overdue schedule
        AmortizationSchedule.objects.create(
            loan=self.loan,
            installment_number=1,
            due_date=timezone.now().date() - timezone.timedelta(days=5), # 5 days overdue
            principal_amount=Decimal('800.00'),
            interest_amount=Decimal('100.00'),
            total_payment=Decimal('900.00'),
            status='pending' # Pending but past due date = overdue
        )
        
        delinquent = LoanReportService.get_delinquent_loans()
        self.assertEqual(len(delinquent), 1)
        self.assertEqual(delinquent[0]['loan'], self.loan)
        self.assertEqual(delinquent[0]['days_overdue'], 5)
        self.assertEqual(delinquent[0]['total_overdue'], Decimal('900.00'))

    def test_get_recent_repayments(self):
        # Create repayment transaction
        Transaction.objects.create(
            account=self.account,
            loan=self.loan,
            transaction_type='payment',
            amount=Decimal('500.00'),
            description='Test Payment'
        )
        
        repayments = LoanReportService.get_recent_repayments()
        self.assertEqual(repayments.count(), 1)
        self.assertEqual(repayments.first().amount, Decimal('500.00'))
