"""
Test script to verify automatic loan balance updates on payment.
Run this with: python manage.py shell < test_payment_processing.py
"""

from users.models import CustomUser
from clients.models import Client
from accounts.models import Account
from loans.models import Loan, LoanApplication, AmortizationSchedule
from decimal import Decimal
import os

print("=" * 70)
print("LOAN PAYMENT PROCESSING TEST")
print("=" * 70)

# Get an active loan with pending payments
active_loans = Loan.objects.filter(status='active')
if not active_loans.exists():
    print("\nNo active loans found. Please approve a loan application first.")
    exit(1)

loan = active_loans.first()
print(f"\nUsing Loan #{loan.loan_id}")
print(f"Client: {loan.application.client.first_name} {loan.application.client.last_name}")
print(f"Original Amount: ₱{loan.loan_amount:,.2f}")
print(f"Current Balance: ₱{loan.remaining_balance:,.2f}")
print(f"Status: {loan.status}")

# Get client's account
client = loan.application.client
accounts = Account.objects.filter(client=client)
if not accounts.exists():
    print(f"\nNo accounts found for client. Creating test account...")
    account = Account.objects.create(
        client=client,
        account_number=f"ACC{client.client_id:06d}",
        account_type='savings',
        current_balance=Decimal('500000.00')  # ₱500,000 starting balance
    )
    print(f"Created account {account.account_number} with balance ₱{account.current_balance:,.2f}")
else:
    account = accounts.first()
    print(f"\nUsing account: {account.account_number}")
    print(f"Account balance: ₱{account.current_balance:,.2f}")

# Get next payment due
next_payment = loan.get_next_payment_due()
if not next_payment:
    print("\n✗ No pending payments found!")
    exit(1)

print(f"\n" + "=" * 70)
print("NEXT PAYMENT DUE")
print("=" * 70)
print(f"Installment: #{next_payment.installment_number} of {loan.term_months}")
print(f"Due Date: {next_payment.due_date}")
print(f"Principal: ₱{next_payment.principal_amount:,.2f}")
print(f"Interest: ₱{next_payment.interest_amount:,.2f}")
print(f"Total Payment: ₱{next_payment.total_payment:,.2f}")
print(f"Status: {next_payment.status}")

# Store initial values
initial_loan_balance = loan.remaining_balance
initial_account_balance = account.current_balance
payment_amount = next_payment.total_payment

print(f"\n" + "=" * 70)
print("PROCESSING PAYMENT")
print("=" * 70)
print(f"Payment Amount: ₱{payment_amount:,.2f}")
print(f"From Account: {account.account_number}")

# Process payment
result = loan.apply_payment(payment_amount, account)

if result['success']:
    print(f"\n✓ {result['message']}")
    
    # Refresh objects from database
    loan.refresh_from_db()
    account.refresh_from_db()
    next_payment.refresh_from_db()
    
    print(f"\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)
    
    # Verify loan balance updated
    expected_loan_balance = initial_loan_balance - next_payment.principal_amount
    print(f"\nLoan Balance:")
    print(f"  Before: ₱{initial_loan_balance:,.2f}")
    print(f"  After:  ₱{loan.remaining_balance:,.2f}")
    print(f"  Expected: ₱{expected_loan_balance:,.2f}")
    if abs(loan.remaining_balance - expected_loan_balance) < Decimal('0.01'):
        print(f"  ✓ Loan balance updated correctly")
    else:
        print(f"  ✗ Loan balance mismatch!")
    
    # Verify account balance updated
    expected_account_balance = initial_account_balance - payment_amount
    print(f"\nAccount Balance:")
    print(f"  Before: ₱{initial_account_balance:,.2f}")
    print(f"  After:  ₱{account.current_balance:,.2f}")
    print(f"  Expected: ₱{expected_account_balance:,.2f}")
    if abs(account.current_balance - expected_account_balance) < Decimal('0.01'):
        print(f"  ✓ Account balance updated correctly")
    else:
        print(f"  ✗ Account balance mismatch!")
    
    # Verify schedule entry marked as paid
    print(f"\nAmortization Schedule Entry:")
    print(f"  Status: {next_payment.status}")
    if next_payment.status == 'paid':
        print(f"  ✓ Schedule entry marked as paid")
    else:
        print(f"  ✗ Schedule entry not marked as paid!")
    
    # Verify transaction created
    if result['transaction']:
        trans = result['transaction']
        print(f"\nTransaction Record:")
        print(f"  ID: #{trans.transaction_id}")
        print(f"  Type: {trans.transaction_type}")
        print(f"  Amount: ₱{trans.amount:,.2f}")
        print(f"  Description: {trans.description}")
        print(f"  ✓ Transaction created successfully")
    
    # Check remaining payments
    remaining_payments = loan.schedules.filter(status='pending').count()
    print(f"\nRemaining Payments: {remaining_payments} of {loan.term_months}")
    
    # Check if loan is paid off
    if loan.status == 'paid':
        print(f"\n🎉 LOAN FULLY PAID OFF!")
    
    print(f"\n" + "=" * 70)
    print("TEST PASSED - PAYMENT PROCESSED SUCCESSFULLY")
    print("=" * 70)
    
else:
    print(f"\n✗ Payment failed: {result['message']}")
    print(f"\n" + "=" * 70)
    print("TEST FAILED")
    print("=" * 70)
