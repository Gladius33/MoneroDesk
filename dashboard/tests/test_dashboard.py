from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

class TestDashboard(TestCase):

    def setUp(self):
        # Create superadmin and staff users
        self.superadmin = User.objects.create_superuser('admin', 'admin@test.com', 'adminpass')
        self.staff_user = User.objects.create_user('staff', 'staff@test.com', 'staffpass')

    def test_superadmin_manage_users(self):
        # Test that superadmin can manage users and assign support staff
        self.client.login(username='admin', password='adminpass')
        response = self.client.post(reverse('assign_support_group'), {'user_id': self.staff_user.id})
        self.assertEqual(response.status_code, 200)

    def test_superadmin_toggle_fees(self):
        # Test that superadmin can toggle fees
        self.client.login(username='admin', password='adminpass')
        response = self.client.post(reverse('toggle_fees'), {'user_id': self.staff_user.id, 'fee_status': 'exempt'})
        self.assertEqual(response.status_code, 200)

    def test_superadmin_manage_permissions(self):
        # Test superadmin managing staff permissions for support
        self.client.login(username='admin', password='adminpass')
        response = self.client.post(reverse('manage_permissions'), {'user_id': self.staff_user.id, 'group': 'Support Staff'})
        self.assertEqual(response.status_code, 200)
