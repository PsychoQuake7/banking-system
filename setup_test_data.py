import os
import django
from decimal import Decimal
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kayamanan.settings')
django.setup()

from django.contrib.auth import get_user_model
from clients.models import Client
from loans.models import Loan, LoanApplication

User = get_user_model()

def create_test_client(username, income, credit_score, first_name, last_name):
    user, created = User.objects.get_or_create(username=username, email=f'{username}@example.com')
    if created:
        user.set_password('TestPass123!')
        user.role = 'borrower'
        user.save()
        print(f"Created user: {username}")
    
    client, created = Client.objects.get_or_create(
        user=user,
        defaults={
            'first_name': first_name,
            'last_name': last_name,
            'date_of_birth': date(1990, 1, 1),
            'address': "Test Address",
            'monthly_income': Decimal(str(income)),
            'credit_score': credit_score
        }
    )
    if not created:
        client.first_name = first_name
        client.last_name = last_name
        client.date_of_birth = date(1990, 1, 1)
        client.address = "Test Address"
        client.monthly_income = Decimal(str(income))
        client.credit_score = credit_score
        client.save()
    print(f"Updated client profile for {username}: Income={income}, Score={credit_score}")
    return client

# High Eligibility Client
client1 = create_test_client('high_eligibility', 100000, 850, 'High', 'Score')

# Low Eligibility Client
client2 = create_test_client('low_eligibility', 20000, 450, 'Low', 'Score')

# Medium Eligibility with Loans
client3 = create_test_client('medium_loans', 50000, 650, 'Medium', 'Loans')

# Create an existing loan for client3
# First create application
app = LoanApplication.objects.create(
    client=client3,
    loan_amount=Decimal('50000'),
    purpose='Personal',
    status='approved',
    eligibility_score=Decimal('70.00')
)

# Create active loan
if not hasattr(app, 'loan'):
    Loan.objects.create(
        application=app,
        loan_amount=Decimal('50000'),
        interest_rate=Decimal('0.10'),
        term_months=12,
        start_date=date.today(),
        end_date=date.today(), # Dummy date
        remaining_balance=Decimal('40000'),
        status='active'
    )
    print(f"Created active loan for {client3.user.username}")

print("Test data setup complete.")
