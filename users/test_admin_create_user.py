from django.test import TestCase, Client
from django.urls import reverse
from users.models import CustomUser

class AdminCreateUserTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = CustomUser.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password123',
            role='admin'
        )
        self.staff_user = CustomUser.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='password123',
            role='staff'
        )
        self.url = reverse('admin_create_user')

    def test_admin_access(self):
        self.client.login(username='admin', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/admin_create_user.html')

    def test_non_admin_access(self):
        self.client.login(username='staff', password='password123')
        response = self.client.get(self.url)
        # Should redirect to login or show 403 depending on configuration, 
        # but user_passes_test usually redirects to login if false.
        self.assertEqual(response.status_code, 302) 

    def test_create_user(self):
        self.client.login(username='admin', password='password123')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'role': 'borrower',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'password123',
            # UserCreationForm requires two password fields by default
            'password_2': 'password123'
        }
        
        # We need to ensure the form validation passes. 
        # UserCreationForm usually requires 'password' and 'password_2'.
        # Let's try sending this data.
        
        # Note: The field names for password in UserCreationForm are 'password' and 'password_2' 
        # if using the standard django.contrib.auth.forms.UserCreationForm.
        # However, looking at the source code of Django, the fields are indeed 'password' and 'password_2'.
        
        # Let's construct the data dictionary properly.
        post_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'role': 'borrower',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'password123',
            'password2': 'password123'
        }
        
        response = self.client.post(self.url, post_data, follow=True)
        
        # Check if user was created
        if not CustomUser.objects.filter(username='newuser').exists():
            print(response.context['form'].errors)
            
        self.assertTrue(CustomUser.objects.filter(username='newuser').exists())
        user = CustomUser.objects.get(username='newuser')
        self.assertEqual(user.role, 'borrower')
        self.assertEqual(user.email, 'newuser@example.com')
        
        # Check for success message
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertIn('created successfully', str(messages[0]))
        
        # Check redirection (follow=True means we end up at the success page, which is the same page)
        self.assertTemplateUsed(response, 'users/admin_create_user.html')
