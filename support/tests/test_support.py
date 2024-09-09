from django.test import TestCase
from django.contrib.auth.models import Group, User
from django.urls import reverse

class TestSupport(TestCase):

    def setUp(self):
        # Create a support group for staff
        self.support_group = Group.objects.create(name='Support Staff')
        self.superadmin = User.objects.create_superuser('admin', 'admin@test.com', 'adminpass')

    def test_support_group_creation(self):
        # Ensure support group can be created by superadmin
        self.client.login(username='admin', password='adminpass')
        response = self.client.post(reverse('create_support_group'))
        self.assertEqual(response.status_code, 200)

    def test_support_can_intervene(self):
        # Test that support can access the support system
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('support_intervene', args=[1]))  # Chatroom ID
        self.assertEqual(response.status_code, 200)

    def test_support_cancel_transaction(self):
        # Test support cancels a transaction
        response = self.client.post(reverse('cancel_transaction', args=[1]))  # Transaction ID
        self.assertEqual(response.status_code, 200)
