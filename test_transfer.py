"""
Test script to verify fund transfer logic.
Run this with: python manage.py shell < test_transfer.py
"""

from users.models import CustomUser
from clients.models import Client
from accounts.models import Account
from transactions.models import Transaction
from decimal import Decimal
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from transactions.views import transfer_create_view
from django.contrib.auth.models import AnonymousUser

print("=" * 70)
print("FUND TRANSFER TEST")
print("=" * 70)

# 1. Setup: Get/Create Source and Target Accounts
# We need a user with a client profile and at least one account
user = CustomUser.objects.filter(role='borrower').first()
if not user or not hasattr(user, 'client'):
    print("No borrower user found. Please create one.")
    exit(1)

client = user.client
source_account = client.accounts.first()

if not source_account:
    print("Borrower has no accounts. Creating one...")
    source_account = Account.objects.create(
        client=client,
        account_number=f"SRC{client.client_id}",
        account_type='savings',
        current_balance=Decimal('1000.00')
    )
else:
    # Ensure sufficient funds
    source_account.current_balance = Decimal('1000.00')
    source_account.save()

# Create a target account (can be same client or different, but must be different account)
target_account = Account.objects.exclude(account_id=source_account.account_id).first()
if not target_account:
    print("No other accounts found for target. Creating one...")
    target_account = Account.objects.create(
        client=client,
        account_number=f"TGT{client.client_id}",
        account_type='checking',
        current_balance=Decimal('0.00')
    )

print(f"\nSource Account: {source_account.account_number} (Balance: ₱{source_account.current_balance})")
print(f"Target Account: {target_account.account_number} (Balance: ₱{target_account.current_balance})")

initial_source_balance = source_account.current_balance
initial_target_balance = target_account.current_balance

# Setup Request Factory
factory = RequestFactory()

# 2. Test Successful Transfer
print("\nTesting Transfer (₱100.00)...")
transfer_amount = Decimal('100.00')

request = factory.post('/transactions/transfer/', {
    'source_account': source_account.account_id,
    'target_account_number': target_account.account_number,
    'amount': transfer_amount,
    'description': 'Test Transfer'
})
request.user = user
setattr(request, 'session', 'session')
messages = FallbackStorage(request)
setattr(request, '_messages', messages)

response = transfer_create_view(request)

# Verify Balances
source_account.refresh_from_db()
target_account.refresh_from_db()

print(f"  Source New Balance: ₱{source_account.current_balance}")
print(f"  Target New Balance: ₱{target_account.current_balance}")

if source_account.current_balance == initial_source_balance - transfer_amount:
    print("  ✓ Source balance decreased correctly")
else:
    print("  ✗ Source balance incorrect!")

if target_account.current_balance == initial_target_balance + transfer_amount:
    print("  ✓ Target balance increased correctly")
else:
    print("  ✗ Target balance incorrect!")

# 3. Test Insufficient Funds
print("\nTesting Insufficient Funds Transfer (₱5000.00)...")
huge_amount = Decimal('5000.00')

request = factory.post('/transactions/transfer/', {
    'source_account': source_account.account_id,
    'target_account_number': target_account.account_number,
    'amount': huge_amount,
    'description': 'Test Huge Transfer'
})
request.user = user
setattr(request, 'session', 'session')
messages = FallbackStorage(request)
setattr(request, '_messages', messages)

response = transfer_create_view(request)

# Verify Balances Unchanged
source_account.refresh_from_db()
target_account.refresh_from_db()

if source_account.current_balance == initial_source_balance - transfer_amount: # Should be same as after first transfer
    print("  ✓ Insufficient funds handled: Source balance unchanged")
else:
    print("  ✗ Failed! Source balance changed unexpectedly")

# 4. Test Invalid Target Account
print("\nTesting Invalid Target Account...")
request = factory.post('/transactions/transfer/', {
    'source_account': source_account.account_id,
    'target_account_number': 'INVALID_ACC_NUM',
    'amount': transfer_amount,
    'description': 'Test Invalid Transfer'
})
request.user = user
setattr(request, 'session', 'session')
messages = FallbackStorage(request)
setattr(request, '_messages', messages)

response = transfer_create_view(request)

# Verify Balances Unchanged
source_account.refresh_from_db()
if source_account.current_balance == initial_source_balance - transfer_amount:
    print("  ✓ Invalid target handled: Source balance unchanged")
else:
    print("  ✗ Failed! Source balance changed unexpectedly")

print("\n" + "=" * 70)
print("TEST COMPLETED")
print("=" * 70)
