"""
Test script to verify loan disbursement workflow.
Run this with: python manage.py shell < test_disbursement.py
"""

from users.models import CustomUser
from clients.models import Client
from accounts.models import Account
from loans.models import Loan, LoanApplication
from transactions.models import Transaction
from decimal import Decimal
from django.utils import timezone

print("=" * 70)
print("LOAN DISBURSEMENT TEST")
print("=" * 70)

# 1. Setup: Get a test loan (undisbursed)
active_loans = Loan.objects.filter(status='active', is_disbursed=False)

if not active_loans.exists():
    print("No active, undisbursed loans found. Creating one for testing...")
    # This part assumes we have a client and application logic, but for simplicity
    # let's try to find ANY active loan and reset its disbursement status if needed
    # OR just use the first active loan and pretend it's new
    loan = Loan.objects.filter(status='active').first()
    if loan:
        loan.is_disbursed = False
        loan.save()
        print(f"Reset disbursement status for Loan #{loan.loan_id}")
    else:
        print("No active loans found at all. Please approve a loan first.")
        exit(1)
else:
    loan = active_loans.first()

print(f"\nUsing Loan #{loan.loan_id}")
print(f"  Amount: ₱{loan.loan_amount}")
print(f"  Client: {loan.application.client}")

# 2. Setup: Get Client Account
client = loan.application.client
account = client.accounts.first()

if not account:
    print("Client has no accounts. Creating one...")
    account = Account.objects.create(
        client=client,
        account_number=f"TEST{client.client_id}",
        account_type='savings',
        current_balance=Decimal('1000.00')
    )

initial_balance = account.current_balance
print(f"\nTarget Account: {account.account_number}")
print(f"  Initial Balance: ₱{initial_balance}")

# 3. Execute Disbursement
print("\nExecuting disbursement...")
result = loan.disburse_funds(account)

print(f"  Result: {result['success']}")
print(f"  Message: {result['message']}")

# 4. Verify Results
if result['success']:
    # Verify Account Balance
    account.refresh_from_db()
    expected_balance = initial_balance + loan.loan_amount
    print(f"\nVerification:")
    print(f"  New Balance: ₱{account.current_balance}")
    
    if account.current_balance == expected_balance:
        print("  ✓ Account balance updated correctly")
    else:
        print(f"  ✗ Balance mismatch! Expected ₱{expected_balance}")

    # Verify Transaction
    transaction = result['transaction']
    if transaction:
        print(f"  Transaction Created: ID #{transaction.transaction_id}")
        print(f"  Type: {transaction.transaction_type}")
        print(f"  Amount: ₱{transaction.amount}")
        
        if transaction.transaction_type == 'disbursement' and transaction.amount == loan.loan_amount:
            print("  ✓ Transaction record correct")
        else:
            print("  ✗ Transaction details incorrect")
    else:
        print("  ✗ No transaction returned")

    # Verify Loan Status
    loan.refresh_from_db()
    print(f"  Loan is_disbursed: {loan.is_disbursed}")
    if loan.is_disbursed:
        print("  ✓ Loan marked as disbursed")
    else:
        print("  ✗ Loan NOT marked as disbursed")

    # 5. Test Double Disbursement Prevention
    print("\nTesting double disbursement prevention...")
    result_2 = loan.disburse_funds(account)
    print(f"  Result: {result_2['success']}")
    print(f"  Message: {result_2['message']}")
    
    if not result_2['success'] and "already been disbursed" in result_2['message']:
        print("  ✓ Double disbursement prevented")
    else:
        print("  ✗ Failed to prevent double disbursement!")

else:
    print("  ✗ Disbursement failed unexpectedly")

print("\n" + "=" * 70)
print("TEST COMPLETED")
print("=" * 70)
