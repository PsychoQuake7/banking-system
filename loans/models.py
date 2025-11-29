from django.db import models
from django.conf import settings
from clients.models import Client
from decimal import Decimal
from datetime import date

class LoanApplication(models.Model):
    STATUS_CHOICES = [
        ('pending','Pending'),
        ('approved','Approved'),
        ('rejected','Rejected'),
    ]

    application_id = models.AutoField(primary_key=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='loan_applications')
    loan_officer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='processed_applications', null=True, blank=True)
    loan_amount = models.DecimalField(max_digits=15, decimal_places=2)
    term_months = models.IntegerField(default=12)
    purpose = models.CharField(max_length=255)
    application_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approval_date = models.DateTimeField(null=True, blank=True)
    eligibility_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    rejection_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"App {self.application_id} - {self.client}"
    
    def calculate_monthly_payment(self, interest_rate: Decimal, term_months: int) -> Decimal:
        """
        Calculate monthly payment for this loan application.
        
        Args:
            interest_rate: Annual interest rate (e.g., 0.12 for 12%)
            term_months: Loan term in months
            
        Returns:
            Monthly payment amount
        """
        if term_months <= 0:
            return Decimal('0.00')
        
        # Convert annual rate to monthly rate
        monthly_rate = interest_rate / 12
        
        if monthly_rate == 0:
            # No interest, simple division
            return self.loan_amount / term_months
        
        # Use amortization formula: M = P * [r(1+r)^n] / [(1+r)^n - 1]
        # Where: M = monthly payment, P = principal, r = monthly rate, n = number of payments
        numerator = monthly_rate * ((1 + monthly_rate) ** term_months)
        denominator = ((1 + monthly_rate) ** term_months) - 1
        
        monthly_payment = self.loan_amount * (numerator / denominator)
        
        return Decimal(str(round(float(monthly_payment), 2)))
    
    def update_eligibility_score(self):
        """
        Recalculate and save eligibility score for this application.
        """
        from loans.utils import calculate_eligibility_score
        
        result = calculate_eligibility_score(self.client, self.loan_amount)
        self.eligibility_score = Decimal(str(result['eligibility_score']))
        self.save(update_fields=['eligibility_score'])
        
        return result

class Loan(models.Model):
    loan_id = models.AutoField(primary_key=True)
    application = models.OneToOneField(LoanApplication, on_delete=models.CASCADE, related_name='loan')
    loan_amount = models.DecimalField(max_digits=15, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=4)
    term_months = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    remaining_balance = models.DecimalField(max_digits=15, decimal_places=2)
    agreement_document = models.FileField(upload_to='loan_agreements/', null=True, blank=True)
    is_disbursed = models.BooleanField(default=False)
    disbursement_date = models.DateTimeField(null=True, blank=True)
    STATUS = [
        ('active','Active'),
        ('paid','Paid'),
        ('default','Default'),
    ]
    status = models.CharField(max_length=20, choices=STATUS, default='active')

    def __str__(self):
        return f"Loan {self.loan_id} - {self.application.client}"
    
    def get_agreement_filename(self):
        """Generate standardized filename for loan agreement"""
        return f"loan_agreement_{self.loan_id}_{self.application.client.client_id}.pdf"

    def get_next_payment_due(self):
        """
        Get the next payment due (overdue or pending).
        
        Returns:
            AmortizationSchedule object or None if no payments due
        """
        # First check for overdue payments
        overdue = self.schedules.filter(status='overdue').order_by('due_date').first()
        if overdue:
            return overdue
            
        # Then check for pending payments
        return self.schedules.filter(status='pending').order_by('due_date').first()
    
    def disburse_funds(self, account):
        """
        Disburse loan funds to the specified account.
        
        Args:
            account: Account to credit funds to
            
        Returns:
            dict with 'success' (bool), 'message' (str), 'transaction' (Transaction or None)
        """
        from transactions.models import Transaction
        from django.db import transaction as db_transaction
        from django.utils import timezone
        
        if self.is_disbursed:
            return {
                'success': False,
                'message': 'Loan has already been disbursed.',
                'transaction': None
            }
            
        if account.client != self.application.client:
            return {
                'success': False,
                'message': 'Target account must belong to the borrower.',
                'transaction': None
            }
            
        try:
            with db_transaction.atomic():
                # Use account.deposit to handle transaction creation and balance update
                transaction = account.deposit(
                    amount=self.loan_amount,
                    description=f'Loan disbursement for Loan #{self.loan_id}',
                    transaction_type='disbursement'
                )
                
                # Link transaction to loan
                transaction.loan = self
                transaction.save()
                
                # Update loan status
                self.is_disbursed = True
                self.disbursement_date = timezone.now()
                self.save()
                
                return {
                    'success': True,
                    'message': f'Successfully disbursed ₱{self.loan_amount:,.2f} to account {account.account_number}.',
                    'transaction': transaction
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'Disbursement failed: {str(e)}',
                'transaction': None
            }

    def apply_payment(self, amount, account):
        """
        Process a loan payment and update balance.
        
        Args:
            amount: Payment amount (Decimal)
            account: Account to deduct payment from
            
        Returns:
            dict with 'success' (bool), 'message' (str), 'transaction' (Transaction or None)
        """
        from transactions.models import Transaction
        from django.db import transaction as db_transaction
        from decimal import Decimal
        
        # Get next pending payment
        next_payment = self.get_next_payment_due()
        if not next_payment:
            return {
                'success': False,
                'message': 'No pending payments found for this loan.',
                'transaction': None
            }
        
        # Validate payment amount
        if amount < next_payment.total_payment:
            return {
                'success': False,
                'message': f'Payment amount must be at least ₱{next_payment.total_payment:,.2f}',
                'transaction': None
            }
        
        # Check account balance
        if account.current_balance < amount:
            return {
                'success': False,
                'message': 'Insufficient funds in account.',
                'transaction': None
            }
        
        # Process payment in atomic transaction
        try:
            with db_transaction.atomic():
                # Create transaction record
                payment_transaction = Transaction.objects.create(
                    account=account,
                    loan=self,
                    transaction_type='payment',
                    amount=amount,
                    description=f'Loan payment #{next_payment.installment_number} for Loan #{self.loan_id}'
                )
                
                # Update account balance
                account.current_balance -= amount
                account.save()
                
                # Update loan remaining balance (subtract principal only)
                self.remaining_balance -= next_payment.principal_amount
                self.save()
                
                # Mark schedule entry as paid
                next_payment.status = 'paid'
                next_payment.save()
                
                # Check if loan is fully paid
                self.check_if_paid_off()
                
                return {
                    'success': True,
                    'message': f'Payment of ₱{amount:,.2f} processed successfully.',
                    'transaction': payment_transaction
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'Payment processing failed: {str(e)}',
                'transaction': None
            }
    
    def check_if_paid_off(self):
        """
        Check if all payments are complete and update loan status if paid off.
        """
        pending_payments = self.schedules.filter(status='pending').count()
        if pending_payments == 0:
            self.status = 'paid'
            self.remaining_balance = Decimal('0.00')
            self.save()
    
    def update_schedule_status(self):
        """
        Update amortization schedule entries to mark overdue payments.
        
        Returns:
            int: Number of payments marked as overdue
        """
        from django.utils import timezone
        today = timezone.now().date()
        
        # Mark overdue payments (pending and past due date)
        overdue_count = self.schedules.filter(
            status='pending',
            due_date__lt=today
        ).update(status='overdue')
        
        return overdue_count
    
    def get_monthly_payment(self) -> Decimal:
        """
        Calculate monthly payment for this loan.
        
        Returns:
            Monthly payment amount
        """
        if self.term_months <= 0:
            return Decimal('0.00')
        
        # Convert annual rate to monthly rate
        monthly_rate = self.interest_rate / 12
        
        if monthly_rate == 0:
            # No interest, simple division
            return self.loan_amount / self.term_months
        
        # Use amortization formula
        numerator = monthly_rate * ((1 + monthly_rate) ** self.term_months)
        denominator = ((1 + monthly_rate) ** self.term_months) - 1
        
        monthly_payment = self.loan_amount * (numerator / denominator)
        
        return Decimal(str(round(float(monthly_payment), 2)))
    
    def is_current(self) -> bool:
        """
        Check if loan payments are up to date (no overdue payments).
        
        Returns:
            True if no overdue payments, False otherwise
        """
        overdue_count = self.schedules.filter(status='overdue').count()
        return overdue_count == 0

class AmortizationSchedule(models.Model):
    schedule_id = models.AutoField(primary_key=True)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='schedules')
    installment_number = models.IntegerField()
    due_date = models.DateField()
    principal_amount = models.DecimalField(max_digits=15, decimal_places=2)
    interest_amount = models.DecimalField(max_digits=15, decimal_places=2)
    total_payment = models.DecimalField(max_digits=15, decimal_places=2)
    STATUS = [
        ('pending','Pending'),
        ('paid','Paid'),
        ('overdue','Overdue'),
    ]
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    reminder_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return f"{self.loan} - Installment {self.installment_number}"

    def is_overdue(self):
        """Check if this payment is overdue."""
        from django.utils import timezone
        if self.status == 'pending':
            return self.due_date < timezone.now().date()
        return self.status == 'overdue'

    @property
    def days_overdue(self):
        """Calculate days overdue (0 if not overdue)."""
        from django.utils import timezone
        if self.is_overdue():
            return (timezone.now().date() - self.due_date).days
        return 0
