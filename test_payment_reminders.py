"""
Test script to verify payment reminder emails.
Run this with: python manage.py shell < test_payment_reminders.py
"""

from users.models import CustomUser
from clients.models import Client
from loans.models import Loan, AmortizationSchedule
from datetime import timedelta
from django.utils import timezone
from django.core.management import call_command
from io import StringIO

print("=" * 70)
print("PAYMENT REMINDER TEST")
print("=" * 70)

# 1. Setup: Get a test loan
active_loans = Loan.objects.filter(status='active')
if not active_loans.exists():
    print("No active loans found. Please approve a loan application first.")
    exit(1)

loan = active_loans.first()
print(f"\nUsing Loan #{loan.loan_id}")

# Ensure user has email
client = loan.application.client
user = client.user
if not user.email:
    user.email = "test_user@example.com"
    user.save()
    print(f"Set test email for user: {user.email}")
else:
    print(f"User email: {user.email}")

# 2. Create a payment due in 3 days
print("\nSetting up a payment due in 3 days...")
target_date = timezone.now().date() + timedelta(days=3)

# Get the first pending schedule
next_payment = loan.schedules.filter(status='pending').order_by('due_date').first()

if not next_payment:
    print("No pending payments found to modify.")
    exit(1)

original_due_date = next_payment.due_date
next_payment.due_date = target_date
next_payment.reminder_sent = False  # Reset flag
next_payment.save()

print(f"Modified Installment #{next_payment.installment_number}")
print(f"  New Due Date: {next_payment.due_date} (Target: {target_date})")
print(f"  Reminder Sent: {next_payment.reminder_sent}")

# 3. Run Management Command
print("\nRunning send_payment_reminders command...")
out = StringIO()
call_command('send_payment_reminders', stdout=out)
output = out.getvalue()

print("\nCommand Output:")
print("-" * 40)
print(output)
print("-" * 40)

# 4. Verify Results
next_payment.refresh_from_db()
print(f"\nVerification:")
print(f"  Reminder Sent Flag: {next_payment.reminder_sent}")

if next_payment.reminder_sent:
    print("  ✓ Reminder sent flag correctly updated to True")
else:
    print("  ✗ Reminder sent flag NOT updated!")

if f"Sent reminder to {user.email}" in output:
    print("  ✓ Output confirms email sent to correct address")
else:
    print("  ✗ Output does not confirm email sent!")

# 5. Test Duplicate Prevention
print("\nTesting duplicate prevention (running command again)...")
out = StringIO()
call_command('send_payment_reminders', stdout=out)
output = out.getvalue()

if "No upcoming payments found requiring reminders" in output or "Found 0 payments" in output:
    print("  ✓ Correctly skipped already reminded payment")
else:
    print("  ✗ Command tried to send reminder again!")
    print(output)

print("\n" + "=" * 70)
print("TEST COMPLETED")
print("=" * 70)
