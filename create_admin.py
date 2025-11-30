
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kayamanan.settings')
django.setup()

from users.models import CustomUser

def create_admin():
    print("Creating admin user...")
    admin, created = CustomUser.objects.get_or_create(
        username='admin_test',
        defaults={
            'email': 'admin@test.com',
            'role': 'admin',
            'is_staff': True,
            'is_superuser': True
        }
    )
    admin.set_password('password123')
    admin.role = 'admin' # Ensure role is set even if user existed
    admin.is_staff = True
    admin.is_superuser = True
    admin.save()
    print(f"Admin User: {admin.username} / password123")

if __name__ == '__main__':
    create_admin()
