"""
Test script to verify transaction logic (deposits and withdrawals).
Run this with: python manage.py shell < test_transactions.py
"""

from users.models import CustomUser
from clients.models import Client
from accounts.models import Account
from transactions.models import Transaction
from decimal import Decimal
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from transactions.views import transaction_create_view
from django.contrib.auth.models import AnonymousUser

print("=" * 70)
print("TRANSACTION LOGIC TEST")
print("=" * 70)

# 1. Setup: Get a test account
account = Account.objects.first()
if not account:
    print("No accounts found. Creating one...")
    # Create client first if needed
    client = Client.objects.first()
    if not client:
        print("No clients found. Please create one.")
        exit(1)
        
    account = Account.objects.create(
        client=client,
        account_number=f"TEST{client.client_id}",
        account_type='savings',
        current_balance=Decimal('1000.00')
    )

print(f"\nUsing Account: {account.account_number}")
initial_balance = account.current_balance
print(f"  Initial Balance: ₱{initial_balance}")

# Setup Request Factory
factory = RequestFactory()
user = CustomUser.objects.filter(role='staff').first()
if not user:
    # Create temp staff user
    user = CustomUser.objects.create_user(username='temp_staff', password='password', role='staff')

# 2. Test Deposit
print("\nTesting Deposit (₱500.00)...")
deposit_amount = Decimal('500.00')
request = factory.post('/transactions/create/', {
    'account_number': account.account_number,
    'transaction_type': 'deposit',
    'amount': deposit_amount,
    'description': 'Test Deposit'
})
request.user = user
setattr(request, 'session', 'session')
messages = FallbackStorage(request)
setattr(request, '_messages', messages)

response = transaction_create_view(request)

# Verify Deposit
account.refresh_from_db()
expected_balance_after_deposit = initial_balance + deposit_amount
print(f"  New Balance: ₱{account.current_balance}")

if account.current_balance == expected_balance_after_deposit:
    print("  ✓ Deposit successful: Balance increased correctly")
else:
    print(f"  ✗ Deposit failed! Expected ₱{expected_balance_after_deposit}")

# Verify Transaction Record
latest_txn = Transaction.objects.filter(account=account).order_by('-transaction_id').first()
if latest_txn and latest_txn.transaction_type == 'deposit' and latest_txn.amount == deposit_amount:
    print("  ✓ Transaction record created correctly")
else:
    print("  ✗ Transaction record missing or incorrect")


# 3. Test Withdrawal
print("\nTesting Withdrawal (₱200.00)...")
withdrawal_amount = Decimal('200.00')
request = factory.post('/transactions/create/', {
    'account_number': account.account_number,
    'transaction_type': 'withdrawal',
    'amount': withdrawal_amount,
    'description': 'Test Withdrawal'
})
request.user = user
setattr(request, 'session', 'session')
messages = FallbackStorage(request)
setattr(request, '_messages', messages)

response = transaction_create_view(request)

# Verify Withdrawal
account.refresh_from_db()
expected_balance_after_withdrawal = expected_balance_after_deposit - withdrawal_amount
print(f"  New Balance: ₱{account.current_balance}")

if account.current_balance == expected_balance_after_withdrawal:
    print("  ✓ Withdrawal successful: Balance decreased correctly")
else:
    print(f"  ✗ Withdrawal failed! Expected ₱{expected_balance_after_withdrawal}")

# Verify Transaction Record
latest_txn = Transaction.objects.filter(account=account).order_by('-transaction_id').first()
if latest_txn and latest_txn.transaction_type == 'withdrawal' and latest_txn.amount == withdrawal_amount:
    print("  ✓ Transaction record created correctly")
else:
    print("  ✗ Transaction record missing or incorrect")


# 4. Test Insufficient Funds
print("\nTesting Insufficient Funds Withdrawal (₱1,000,000.00)...")
huge_amount = Decimal('1000000.00')
request = factory.post('/transactions/create/', {
    'account_number': account.account_number,
    'transaction_type': 'withdrawal',
    'amount': huge_amount,
    'description': 'Test Huge Withdrawal'
})
request.user = user
setattr(request, 'session', 'session')
messages = FallbackStorage(request)
setattr(request, '_messages', messages)

response = transaction_create_view(request)

# Verify Balance Unchanged
account.refresh_from_db()
print(f"  New Balance: ₱{account.current_balance}")

if account.current_balance == expected_balance_after_withdrawal:
    print("  ✓ Insufficient funds handled: Balance unchanged")
else:
    print("  ✗ Failed! Balance changed unexpectedly")

print("\n" + "=" * 70)
print("TEST COMPLETED")
print("=" * 70)
