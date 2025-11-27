from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword', email='test@example.com')

    def test_login_page_loads(self):
        response = self.client.get(reverse('account_login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/login.html')

    def test_signup_page_loads(self):
        response = self.client.get(reverse('account_signup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/signup.html')

    def test_login_successful(self):
        response = self.client.post(reverse('account_login'), {
            'login': 'testuser',
            'password': 'testpassword'
        })
        # Should redirect to dashboard
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_logout_successful(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.post(reverse('account_logout'))
        # Should redirect to login or home, depending on settings. 
        # Settings say LOGOUT_REDIRECT_URL = 'account_login'
        self.assertRedirects(response, reverse('account_login'))
        self.assertFalse(response.wsgi_request.user.is_authenticated)
