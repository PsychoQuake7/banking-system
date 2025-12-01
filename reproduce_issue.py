
import os
import django
from django.test import Client as TestClient
from django.contrib.auth import get_user_model
from django.urls import reverse
from datetime import date
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kayamanan.settings')
django.setup()

from django.conf import settings
settings.ALLOWED_HOSTS += ['testserver']

from clients.models import Client

def reproduce():
    User = get_user_model()
    
    # Create users
    admin_user, _ = User.objects.get_or_create(username='admin', defaults={'email': 'admin@example.com', 'role': 'admin'})
    if not admin_user.check_password('password'):
        admin_user.set_password('password')
        admin_user.save()
        
    staff_user, _ = User.objects.get_or_create(username='staff', defaults={'email': 'staff@example.com', 'role': 'staff'})
    if not staff_user.check_password('password'):
        staff_user.set_password('password')
        staff_user.save()
        
    borrower_user, _ = User.objects.get_or_create(username='borrower', defaults={'email': 'borrower@example.com', 'role': 'borrower'})
    if not borrower_user.check_password('password'):
        borrower_user.set_password('password')
        borrower_user.save()
    
    # Create client for borrower
    client = Client.objects.create(
        user=borrower_user,
        first_name='Original',
        last_name='Name',
        date_of_birth=date(1990, 1, 1),
        address='Original Address',
        monthly_income=Decimal('50000.00'),
        credit_score=700
    )
    
    c = TestClient()
    
    print("--- Testing Staff Access ---")
    c.login(username='staff', password='password')
    url = reverse('clients:client_edit', args=[client.client_id])
    response = c.get(url)
    
    if response.status_code == 403:
        print(f"SUCCESS: Staff cannot access client edit view (Status {response.status_code})")
    else:
        print(f"FAIL: Staff can access client edit view (Status {response.status_code})")
        
    # Try to update as staff
    data = {
        'first_name': 'Updated',
        'last_name': 'Name',
        'email': 'borrower@example.com',
        'date_of_birth': '1990-01-01',
        'address': 'Updated Address',
        'monthly_income': '60000',
        'credit_score': '750'
    }
    response = c.post(url, data)
    
    if response.status_code == 403:
        print("SUCCESS: Staff cannot update client data (Status 403)")
    else:
        print(f"FAIL: Staff can update client data (Status {response.status_code})")
    
    client.refresh_from_db()
    if client.first_name == 'Original':
        print("INFO: Client data was NOT updated")
    else:
        print("FAIL: Client data WAS updated")
        
    print("\n--- Testing Admin Access ---")
    c.login(username='admin', password='password')
    response = c.get(url)
    
    if response.status_code == 200:
        print("INFO: Admin can access client edit view (Status 200)")
    else:
        print(f"FAIL: Admin cannot access client edit view (Status {response.status_code})")

    # Clean up
    client.delete()
    admin_user.delete()
    staff_user.delete()
    borrower_user.delete()

if __name__ == '__main__':
    reproduce()
