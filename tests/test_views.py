from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

class DashboardTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_user_dashboard_view(self):
        response = self.client.get(reverse('user_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')

    def test_email_change(self):
        response = self.client.post(reverse('profile'), {
            'email': 'newemail@example.com'
        })
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'newemail@example.com')

    def test_password_change(self):
        response = self.client.post(reverse('profile'), {
            'old_password': '12345',
            'new_password1': 'new_password',
            'new_password2': 'new_password',
        })
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        login_response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'new_password'
        })
        self.assertEqual(login_response.status_code, 200)
