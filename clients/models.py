from django.db import models
from django.conf import settings
from django.db.models import Sum
from decimal import Decimal

class Client(models.Model):
    client_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    address = models.TextField()
    # prefer FileField for uploads rather than storing simple path
    id_document = models.FileField(upload_to='client_documents/', blank=True, null=True)
    credit_score = models.IntegerField(default=0)
    monthly_income = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.user.username})"
    
    def get_active_loans(self):
        """
        Get all active loans for this client.
        
        Returns:
            QuerySet of active Loan objects
        """
        from loans.models import Loan
        return Loan.objects.filter(
            application__client=self,
            status='active'
        )
    
    def get_total_loan_balance(self) -> Decimal:
        """
        Calculate total remaining balance across all active loans.
        
        Returns:
            Total balance as Decimal
        """
        active_loans = self.get_active_loans()
        total = active_loans.aggregate(total=Sum('remaining_balance'))['total']
        return total or Decimal('0.00')
    
    def get_monthly_loan_payments(self) -> Decimal:
        """
        Calculate total monthly payments across all active loans.
        
        Returns:
            Total monthly payments as Decimal
        """
        active_loans = self.get_active_loans()
        total_monthly = Decimal('0.00')
        
        for loan in active_loans:
            total_monthly += loan.get_monthly_payment()
        
        return total_monthly
    
    def get_debt_to_income_ratio(self) -> float:
        """
        Calculate debt-to-income ratio as percentage.
        
        Returns:
            DTI ratio as float (0-100+)
        """
        if self.monthly_income <= 0:
            return 100.0
        
        monthly_debt = self.get_monthly_loan_payments()
        dti = (monthly_debt / self.monthly_income) * 100
        
        return round(float(dti), 2)
    
    def check_loan_eligibility(self, requested_amount=None):
        """
        Check loan eligibility for this client.
        
        Args:
            requested_amount: Optional requested loan amount
            
        Returns:
            Dictionary with eligibility details from calculate_eligibility_score()
        """
        from loans.utils import calculate_eligibility_score
        return calculate_eligibility_score(self, requested_amount)
