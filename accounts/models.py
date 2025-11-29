from django.db import models
from clients.models import Client

class Account(models.Model):
    ACCOUNT_TYPES = [
        ('savings', 'Savings'),
        ('checking', 'Checking'),
    ]

    account_id = models.AutoField(primary_key=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='accounts')
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    account_number = models.CharField(max_length=20, unique=True)
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.0000)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.account_number} - {self.client}"

    def deposit(self, amount, description=None, transaction_type='deposit'):
        """
        Increases balance and creates a transaction record.
        """
        from transactions.models import Transaction
        from django.db import transaction
        
        with transaction.atomic():
            self.current_balance += amount
            self.save()
            
            return Transaction.objects.create(
                account=self,
                transaction_type=transaction_type,
                amount=amount,
                description=description or f"{transaction_type.title()} of {amount}"
            )

    def withdraw(self, amount, description=None, transaction_type='withdrawal'):
        """
        Decreases balance and creates a transaction record.
        Raises ValueError if insufficient funds.
        """
        from transactions.models import Transaction
        from django.db import transaction
        
        if self.current_balance < amount:
            raise ValueError(f"Insufficient funds. Balance: {self.current_balance}")

        with transaction.atomic():
            self.current_balance -= amount
            self.save()
            
            return Transaction.objects.create(
                account=self,
                transaction_type=transaction_type,
                amount=amount,
                description=description or f"{transaction_type.title()} of {amount}"
            )

    def compute_daily_interest(self, date=None):
        """
        Calculates daily interest based on current balance and interest rate.
        Creates an InterestAccrual record.
        """
        from django.utils import timezone
        from decimal import Decimal
        
        if self.account_type != 'savings':
            return None
            
        if not date:
            date = timezone.now().date()
            
        # Check if accrual already exists for this date
        if self.accruals.filter(accrual_date=date).exists():
            return None
            
        # Formula: Balance * (Rate / 365)
        # Rate is stored as decimal (e.g., 0.05 for 5%)
        daily_rate = self.interest_rate / Decimal('365')
        interest = self.current_balance * daily_rate
        
        # Round to 2 decimal places for storage
        interest = interest.quantize(Decimal('0.01'))
        
        if interest <= 0:
            return None
            
        return InterestAccrual.objects.create(
            account=self,
            accrual_date=date,
            interest_earned=interest,
            balance_snapshot=self.current_balance,
            is_compounded=False
        )

    def capitalize_interest(self):
        """
        Sums up all uncompounded interest and deposits it into the account.
        """
        from django.db import transaction
        from django.db.models import Sum
        from decimal import Decimal
        
        with transaction.atomic():
            # Get uncompounded interest
            uncompounded = self.accruals.filter(is_compounded=False)
            total_interest = uncompounded.aggregate(Sum('interest_earned'))['interest_earned__sum'] or Decimal('0.00')
            
            if total_interest > 0:
                # Deposit interest
                self.deposit(
                    total_interest, 
                    description=f"Interest Capitalization",
                    transaction_type='deposit' # Could be 'interest' if added to choices
                )
                
                # Mark as compounded
                uncompounded.update(is_compounded=True)
                
                return total_interest
            return Decimal('0.00')

class InterestAccrual(models.Model):
    accrual_id = models.AutoField(primary_key=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='accruals')
    accrual_date = models.DateField()
    interest_earned = models.DecimalField(max_digits=15, decimal_places=2)
    balance_snapshot = models.DecimalField(max_digits=15, decimal_places=2)
    is_compounded = models.BooleanField(default=False)

    class Meta:
        ordering = ['-accrual_date']

    def __str__(self):
        return f"{self.account.account_number} - {self.accrual_date} - {self.interest_earned}"
