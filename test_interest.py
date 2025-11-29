"""
Test script to verify interest computation logic.
Run this with: python manage.py shell < test_interest.py
"""

from users.models import CustomUser
from clients.models import Client
from accounts.models import Account, InterestAccrual
from decimal import Decimal
from django.utils import timezone
import datetime

print("=" * 70)
print("INTEREST COMPUTATION TEST")
print("=" * 70)

# 1. Setup: Get/Create Savings Account
user = CustomUser.objects.filter(role='borrower').first()
if not user or not hasattr(user, 'client'):
    print("No borrower user found. Please create one.")
    exit(1)

client = user.client
account = Account.objects.filter(client=client, account_type='savings').first()

if not account:
    print("Creating savings account...")
    account = Account.objects.create(
        client=client,
        account_number=f"SAV{client.client_id}",
        account_type='savings',
        current_balance=Decimal('10000.00'),
        interest_rate=Decimal('0.05') # 5% APY
    )
else:
    # Reset for test
    account.current_balance = Decimal('10000.00')
    account.interest_rate = Decimal('0.05')
    account.save()
    # Clear existing accruals for today
    InterestAccrual.objects.filter(account=account, accrual_date=timezone.now().date()).delete()

print(f"\nAccount: {account.account_number}")
print(f"Balance: ₱{account.current_balance}")
print(f"Interest Rate: {account.interest_rate * 100}%")

# 2. Test Daily Accrual
print("\nTesting Daily Accrual...")
today = timezone.now().date()

# Expected Interest: 10000 * (0.05 / 365) = 1.369... -> 1.37
expected_interest = (account.current_balance * (account.interest_rate / Decimal('365'))).quantize(Decimal('0.01'))
print(f"  Expected Daily Interest: ₱{expected_interest}")

accrual = account.compute_daily_interest(date=today)

if accrual:
    print(f"  Actual Accrued Interest: ₱{accrual.interest_earned}")
    if accrual.interest_earned == expected_interest:
        print("  ✓ Daily interest calculated correctly")
    else:
        print(f"  ✗ Interest mismatch! Expected {expected_interest}, got {accrual.interest_earned}")
else:
    print("  ✗ No interest accrued (maybe already exists or zero balance?)")

# 3. Test Capitalization
print("\nTesting Capitalization...")
initial_balance = account.current_balance

# Run capitalization
capitalized_amount = account.capitalize_interest()

print(f"  Capitalized Amount: ₱{capitalized_amount}")

# Verify Balance Update
account.refresh_from_db()
print(f"  New Balance: ₱{account.current_balance}")

if account.current_balance == initial_balance + capitalized_amount:
    print("  ✓ Balance updated correctly")
else:
    print("  ✗ Balance update failed!")

# Verify Accrual Status
accrual.refresh_from_db()
if accrual.is_compounded:
    print("  ✓ Accrual marked as compounded")
else:
    print("  ✗ Accrual NOT marked as compounded")

print("\n" + "=" * 70)
print("TEST COMPLETED")
print("=" * 70)
