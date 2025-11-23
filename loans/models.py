from django.db import models
from django.conf import settings
from clients.models import Client

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
