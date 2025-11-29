"""
Test script to verify automatic amortization schedule status updates.
Run this with: python manage.py shell < test_overdue_status.py
"""

from users.models import CustomUser
from clients.models import Client
from accounts.models import Account
from loans.models import Loan, LoanApplication, AmortizationSchedule
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone

print("=" * 70)
print("AMORTIZATION STATUS UPDATE TEST")
print("=" * 70)

# 1. Setup: Get or create a test loan
active_loans = Loan.objects.filter(status='active')
if not active_loans.exists():
    print("No active loans found. Please approve a loan application first.")
    exit(1)

loan = active_loans.first()
print(f"\nUsing Loan #{loan.loan_id}")

# CLEANUP: Pay off any existing overdue payments to ensure clean state
print("\nChecking for existing overdue payments...")
overdue_payments = loan.schedules.filter(status='overdue')
if overdue_payments.exists():
    print(f"Found {overdue_payments.count()} existing overdue payments. Cleaning up...")
    
    # Get client account
    client = loan.application.client
    account = client.accounts.first()
    if not account:
        account = Account.objects.create(
            client=client,
            account_number=f"TEST{client.client_id}",
            account_type='savings',
            current_balance=Decimal('1000000.00')
        )
    
    for payment in overdue_payments:
        print(f"Paying off overdue installment #{payment.installment_number}")
        # Ensure balance
        if account.current_balance < payment.total_payment:
            account.current_balance += payment.total_payment + 1000
            account.save()
            
        loan.apply_payment(payment.total_payment, account)

print("Cleanup complete. No overdue payments remaining.")


# 2. Create a fake past due payment
print("\nCreating a past due payment for testing...")
past_due_date = timezone.now().date() - timedelta(days=5)

# Get the first pending schedule
next_payment = loan.schedules.filter(status='pending').order_by('due_date').first()

if not next_payment:
    print("No pending payments found to modify.")
    exit(1)

original_due_date = next_payment.due_date
next_payment.due_date = past_due_date
next_payment.save()

print(f"Modified Installment #{next_payment.installment_number}")
print(f"  New Due Date: {next_payment.due_date} (5 days ago)")
print(f"  Current Status: {next_payment.status}")

# 3. Trigger Status Update
print("\nTriggering status update...")
overdue_count = loan.update_schedule_status()
print(f"  Result: Marked {overdue_count} payments as overdue")

# 4. Verify Status Change
next_payment.refresh_from_db()
print(f"\nVerifying status change:")
print(f"  Status: {next_payment.status}")
print(f"  Is Overdue: {next_payment.is_overdue()}")
print(f"  Days Overdue: {next_payment.days_overdue}")

if next_payment.status == 'overdue' and next_payment.days_overdue == 5:
    print("  ✓ Status correctly updated to 'overdue'")
    print("  ✓ Days overdue calculated correctly (5 days)")
else:
    print("  ✗ Status update failed!")
    print(f"    Expected: overdue, 5 days")
    print(f"    Actual: {next_payment.status}, {next_payment.days_overdue} days")

# 5. Test Payment of Overdue Installment
print("\nTesting payment of overdue installment...")

# Get client account (again, just in case)
client = loan.application.client
account = client.accounts.first()
if not account:
    account = Account.objects.create(
        client=client,
        account_number=f"TEST{client.client_id}",
        account_type='savings',
        current_balance=Decimal('100000.00')
    )

# Ensure enough balance
if account.current_balance < next_payment.total_payment:
    account.current_balance += next_payment.total_payment + 1000
    account.save()

print(f"Paying ₱{next_payment.total_payment} from account {account.account_number}")
result = loan.apply_payment(next_payment.total_payment, account)

if result['success']:
    print(f"  ✓ Payment successful: {result['message']}")
    
    # We need to verify that THIS specific payment was paid
    # Since we cleaned up, this should be the only overdue one (or the first one)
    next_payment.refresh_from_db()
    print(f"  New Status: {next_payment.status}")
    
    if next_payment.status == 'paid':
        print("  ✓ Overdue payment correctly marked as 'paid'")
    else:
        print(f"  ✗ Failed to mark overdue payment as paid. Status: {next_payment.status}")
        
        # Debug: check what WAS paid
        if result['transaction']:
            print(f"  Transaction Description: {result['transaction'].description}")
else:
    print(f"  ✗ Payment failed: {result['message']}")

print("\n" + "=" * 70)
print("TEST COMPLETED")
print("=" * 70)
