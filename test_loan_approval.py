"""
Manual test script to verify loan agreement PDF generation.
Run this with: python manage.py shell < test_loan_approval.py
"""

from users.models import CustomUser
from clients.models import Client
from loans.models import LoanApplication, Loan
from decimal import Decimal
from datetime import date
from dateutil.relativedelta import relativedelta
import os
from django.conf import settings

print("=" * 60)
print("LOAN AGREEMENT GENERATION TEST")
print("=" * 60)

# Get a pending loan application
pending_apps = LoanApplication.objects.filter(status='pending')
if not pending_apps.exists():
    print("\nNo pending applications found. Creating test application...")
    client = Client.objects.first()
    if not client:
        print("ERROR: No clients found in database")
        exit(1)
    
    app = LoanApplication.objects.create(
        client=client,
        loan_amount=Decimal('50000.00'),
        term_months=12,
        purpose='Test Loan for PDF Generation'
    )
    app.update_eligibility_score()
    print(f"Created test application #{app.application_id}")
else:
    app = pending_apps.first()
    print(f"\nUsing existing application #{app.application_id}")

print(f"Client: {app.client.first_name} {app.client.last_name}")
print(f"Amount: ₱{app.loan_amount}")
print(f"Term: {app.term_months} months")
print(f"Status: {app.status}")

# Get admin user
admin = CustomUser.objects.filter(role='admin').first()
if not admin:
    print("\nERROR: No admin user found")
    exit(1)

print(f"\nApproving with user: {admin.username}")

# Approve the application
app.status = 'approved'
app.approval_date = date.today()
app.loan_officer = admin
app.save()

# Create loan
interest_rate = Decimal('0.12')
start_date = date.today()
end_date = start_date + relativedelta(months=app.term_months)

loan = Loan.objects.create(
    application=app,
    loan_amount=app.loan_amount,
    interest_rate=interest_rate,
    term_months=app.term_months,
    start_date=start_date,
    end_date=end_date,
    remaining_balance=app.loan_amount,
    status='active'
)

print(f"\nCreated Loan #{loan.loan_id}")
print(f"Interest Rate: {float(interest_rate * 100)}%")
print(f"Monthly Payment: ₱{loan.get_monthly_payment()}")

# Generate PDF
print("\n" + "=" * 60)
print("GENERATING LOAN AGREEMENT PDF")
print("=" * 60)

try:
    from loans.document_generator import generate_loan_agreement
    
    agreement_path = generate_loan_agreement(loan)
    loan.agreement_document = agreement_path
    loan.save()
    
    full_path = os.path.join(settings.MEDIA_ROOT, agreement_path)
    file_size = os.path.getsize(full_path)
    
    print(f"\n✓ PDF generated successfully!")
    print(f"  Path: {agreement_path}")
    print(f"  Full path: {full_path}")
    print(f"  File size: {file_size:,} bytes")
    print(f"  Filename: {loan.get_agreement_filename()}")
    
    print("\n" + "=" * 60)
    print("TEST PASSED - PDF GENERATION SUCCESSFUL")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ PDF generation failed!")
    print(f"  Error: {str(e)}")
    import traceback
    traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("TEST FAILED")
    print("=" * 60)
