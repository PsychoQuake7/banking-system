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
