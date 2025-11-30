from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import AuditLog
from .utils import get_client_ip
from datetime import datetime, timedelta

User = get_user_model()

class AuditMiddlewareTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            role='admin'
        )
        self.client.login(username='testuser', password='password123')
    
    def test_middleware_logs_post_request(self):
        """Test that POST requests are logged"""
        initial_count = AuditLog.objects.count()
        
        # Make a POST request (e.g., to a form)
        response = self.client.post(reverse('account_login'), {
            'login': 'testuser',
            'password': 'password123'
        })
        
        # Check that a log was created
        self.assertGreater(AuditLog.objects.count(), initial_count)
        
        # Verify log details
        log = AuditLog.objects.latest('timestamp')
        self.assertEqual(log.user, self.user)
        self.assertIn('POST', log.action)
        self.assertIsNotNone(log.ip_address)
    
    def test_middleware_skips_get_requests(self):
        """Test that GET requests are not logged"""
        initial_count = AuditLog.objects.count()
        
        # Make a GET request
        response = self.client.get(reverse('dashboard'))
        
        # Count should not increase
        # (might increase if there are redirects with POST, so we check the action)
        if AuditLog.objects.count() > initial_count:
            latest_log = AuditLog.objects.latest('timestamp')
            self.assertNotIn('GET', latest_log.action)
    
    def test_ip_extraction(self):
        """Test IP address extraction utility"""
        from django.test import RequestFactory
        
        factory = RequestFactory()
        
        # Test with REMOTE_ADDR
        request = factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        ip = get_client_ip(request)
        self.assertEqual(ip, '192.168.1.1')
        
        # Test with X-Forwarded-For
        request = factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.1, 192.168.1.1'
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        ip = get_client_ip(request)
        self.assertEqual(ip, '10.0.0.1')  # Should get the first IP

class AuditViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='password123',
            role='staff',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='password123',
            role='borrower'
        )
        
        # Create some audit logs
        for i in range(5):
            AuditLog.objects.create(
                user=self.staff_user,
                action=f'POST /test/{i}',
                ip_address='127.0.0.1',
                details=f'Test log {i}'
            )
    
    def test_audit_logs_view_requires_staff(self):
        """Test that only staff can access audit logs"""
        # Try as regular user
        self.client.login(username='regularuser', password='password123')
        response = self.client.get(reverse('audit:audit_logs'))
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Try as staff
        self.client.login(username='staffuser', password='password123')
        response = self.client.get(reverse('audit:audit_logs'))
        self.assertEqual(response.status_code, 200)
    
    def test_audit_logs_filtering_by_user(self):
        """Test filtering logs by user"""
        self.client.login(username='staffuser', password='password123')
        
        response = self.client.get(reverse('audit:audit_logs'), {
            'user': self.staff_user.id
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        
        # All logs should be from staff_user
        for log in response.context['page_obj']:
            self.assertEqual(log.user, self.staff_user)
    
    def test_audit_logs_filtering_by_action(self):
        """Test filtering logs by action"""
        self.client.login(username='staffuser', password='password123')
        
        response = self.client.get(reverse('audit:audit_logs'), {
            'action': 'POST /test/1'
        })
        
        self.assertEqual(response.status_code, 200)
        # Should find the specific log
        logs = list(response.context['page_obj'])
        self.assertTrue(any('POST /test/1' in log.action for log in logs))
    
    def test_csv_export(self):
        """Test CSV export functionality"""
        self.client.login(username='staffuser', password='password123')
        
        response = self.client.get(reverse('audit:export_csv'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        
        # Check content
        content = response.content.decode('utf-8')
        self.assertIn('Log ID', content)
        self.assertIn('User', content)
    
    def test_excel_export(self):
        """Test Excel export functionality"""
        self.client.login(username='staffuser', password='password123')
        
        response = self.client.get(reverse('audit:export_excel'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertIn('attachment', response['Content-Disposition'])
