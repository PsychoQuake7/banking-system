from django.db import models
from accounts.models import Account
from transactions.models import Transaction

class GLAccount(models.Model):
    ACCOUNT_TYPES = [
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('revenue', 'Revenue'),
        ('expense', 'Expense'),
    ]

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    description = models.TextField(blank=True, null=True)
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.name} ({self.get_account_type_display()})"

class LedgerEntry(models.Model):
    DEBIT_CREDIT_CHOICES = [
        ('debit', 'Debit'),
        ('credit', 'Credit'),
    ]

    entry_id = models.AutoField(primary_key=True)
    transaction_ref = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_entries')
    gl_account = models.ForeignKey(GLAccount, on_delete=models.PROTECT, related_name='entries')
    client_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_entries')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    debit_credit = models.CharField(max_length=10, choices=DEBIT_CREDIT_CHOICES)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Ledger Entries"
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['gl_account']),
        ]

    def __str__(self):
        return f"{self.created_at.date()} - {self.gl_account.code} - {self.debit_credit.title()} {self.amount}"
