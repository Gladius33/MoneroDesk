from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.contrib.auth import get_user_model

class TestDashboard(TestCase):

    def setUp(self):
        # Create superadmin and staff users
        self.superadmin = User.objects.create_superuser('admin', 'admin@test.com', 'adminpass')
        self.staff_user = User.objects.create_user('staff', 'staff@test.com', 'staffpass')
        self.support_group = Group.objects.create(name="Support")
        
    def test_superadmin_access_dashboard(self):
        # Test that superadmin can access the admin dashboard
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/admin_dashboard.html')

    def test_staff_access_restricted_dashboard(self):
        # Test that non-superadmin staff cannot access the admin dashboard
        self.client.login(username='staff', password='staffpass')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 302)  # Should redirect due to lack of permissions

    def test_superadmin_manage_support_group(self):
        # Test that superadmin can manage the support group
        self.client.login(username='admin', password='adminpass')
        response = self.client.post(reverse('manage_support_group'), {'support_group': [self.staff_user.id]})
        self.assertEqual(response.status_code, 302)  # Should redirect after successful form submission
        self.assertTrue(self.support_group.user_set.filter(id=self.staff_user.id).exists())

    def test_superadmin_toggle_fee_exemptions(self):
        # Test that superadmin can toggle fee exemptions
        self.client.login(username='admin', password='adminpass')
        response = self.client.post(reverse('manage_fee_exemptions'), {'user_id': self.staff_user.id})
        self.assertEqual(response.status_code, 302)  # Should redirect after toggling fee exemption
        self.staff_user.refresh_from_db()
        self.assertTrue(self.staff_user.profile.is_first_100)

    def test_superadmin_manage_referral_fees(self):
        # Test that superadmin can update referral fees
        self.client.login(username='admin', password='adminpass')
        response = self.client.post(reverse('manage_referral_fees'), {'referral_percentage': '2.5'})
        self.assertEqual(response.status_code, 302)
        # Add assertions to verify that the referral percentage was updated
