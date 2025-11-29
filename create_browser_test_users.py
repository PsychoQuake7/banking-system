
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kayamanan.settings')
django.setup()

from users.models import CustomUser
from clients.models import Client
from accounts.models import Account

def create_test_users():
    print("Creating test users for browser verification...")

    # 1. Staff User
    staff, created = CustomUser.objects.get_or_create(
        username='staff_test',
        defaults={'email': 'staff@test.com', 'role': 'staff'}
    )
    staff.set_password('password123')
    staff.save()
    print(f"Staff User: {staff.username} / password123")

    # 2. Borrower User
    borrower, created = CustomUser.objects.get_or_create(
        username='borrower_test',
        defaults={'email': 'borrower@test.com', 'role': 'borrower'}
    )
    borrower.set_password('password123')
    borrower.save()
    print(f"Borrower User: {borrower.username} / password123")

    # 3. Client Profile
    client, created = Client.objects.get_or_create(
        user=borrower,
        defaults={
            'first_name': 'Test',
            'last_name': 'Borrower',
            'date_of_birth': '1990-01-01',
            'address': '123 Test St',
            'monthly_income': Decimal('50000.00')
        }
    )

    # 4. Accounts
    # Savings (Source)
    savings, created = Account.objects.get_or_create(
        client=client,
        account_type='savings',
        defaults={'account_number': 'SAV-001', 'current_balance': Decimal('5000.00')}
    )
    if not created:
        savings.current_balance = Decimal('5000.00')
        savings.save()
    print(f"Savings Account: {savings.account_number} (Balance: {savings.current_balance})")

    # Checking (Target)
    checking, created = Account.objects.get_or_create(
        client=client,
        account_type='checking',
        defaults={'account_number': 'CHK-001', 'current_balance': Decimal('0.00')}
    )
    if not created:
        checking.current_balance = Decimal('0.00')
        checking.save()
    print(f"Checking Account: {checking.account_number} (Balance: {checking.current_balance})")

if __name__ == '__main__':
    create_test_users()
