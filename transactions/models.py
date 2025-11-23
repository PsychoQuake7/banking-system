from django.db import models
from accounts.models import Account
from loans.models import Loan  # loan is optional, circular import avoided if app order correct

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('deposit','Deposit'),
        ('withdrawal','Withdrawal'),
        ('payment','Payment'),
        ('disbursement','Disbursement'),
    ]

    transaction_id = models.AutoField(primary_key=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    loan = models.ForeignKey('loans.Loan', on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} ({self.account.account_number})"
