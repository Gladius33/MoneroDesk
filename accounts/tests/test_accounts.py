from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

class TestAccounts(TestCase):

    def setUp(self):
        # Create initial user data
        self.user = User.objects.create_user('testuser', 'user@test.com', 'testpass')

    def test_user_registration_with_referral(self):
        # Test user registration with referral code
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password1': 'newpass',
            'password2': 'newpass',
            'referral_code': 'REF123'
        })
        self.assertEqual(response.status_code, 200)

    def test_notification_system(self):
        # Test that users receive notifications
        response = self.client.get(reverse('notifications'))
        self.assertEqual(response.status_code, 200)

    def test_manage_user_wallet(self):
        # Test user wallet updates (email, password)
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(reverse('change_email'), {'email': 'newemail@test.com'})
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('change_password'), {
            'old_password': 'testpass',
            'new_password1': 'newpass',
            'new_password2': 'newpass'
        })
        self.assertEqual(response.status_code, 200)
