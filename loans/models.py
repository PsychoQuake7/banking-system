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
    loan_officer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='processed_applications')
    loan_amount = models.DecimalField(max_digits=15, decimal_places=2)
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
    STATUS = [
        ('active','Active'),
        ('paid','Paid'),
        ('default','Default'),
    ]
    status = models.CharField(max_length=20, choices=STATUS, default='active')

    def __str__(self):
        return f"Loan {self.loan_id} - {self.application.client}"
    
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

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return f"{self.loan} - Installment {self.installment_number}"
