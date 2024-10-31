from django.test import TestCase
from django.contrib.auth.models import Group, User
from django.urls import reverse
from django.utils import timezone
from support.models import SupportRequest
from transactions.models import Transaction
from datetime import timedelta

class TestSupport(TestCase):

    def setUp(self):
        # Create users, groups, and initial transaction
        self.support_group = Group.objects.create(name='Support')
        self.superadmin = User.objects.create_superuser('admin', 'admin@test.com', 'adminpass')
        self.support_agent = User.objects.create_user('support', 'support@test.com', 'supportpass')
        self.support_agent.groups.add(self.support_group)

        self.buyer = User.objects.create_user('buyer', 'buyer@test.com', 'buyerpass')
        self.seller = User.objects.create_user('seller', 'seller@test.com', 'sellerpass')

        # Create a transaction
        self.transaction = Transaction.objects.create(
            buyer=self.buyer,
            seller=self.seller,
            transaction_amount=100,
            status='pending',
            created_at=timezone.now() - timedelta(hours=1)
        )

        # Create a support request linked to the transaction
        self.support_request = SupportRequest.objects.create(
            transaction=self.transaction,
            status='waiting',
        )

    def test_support_group_creation(self):
        """Ensure superadmin can create the support group."""
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('support_dashboard'))  # Adjust if necessary
        self.assertEqual(response.status_code, 200)

    def test_support_can_intervene(self):
        """Ensure support staff can join the chat and intervene."""
        self.client.login(username='support', password='supportpass')
        response = self.client.get(reverse('join_chat', args=[self.support_request.id]))
        self.assertEqual(response.status_code, 200)

    def test_support_can_cancel_transaction(self):
        """Test that support can cancel a transaction."""
        self.client.login(username='support', password='supportpass')
        response = self.client.post(reverse('cancel_transaction_by_support', args=[self.support_request.id]))
        self.assertEqual(response.status_code, 200)
        self.support_request.refresh_from_db()
        self.assertEqual(self.support_request.transaction.status, 'canceled')

    def test_support_can_validate_transaction(self):
        """Test that support can validate and complete a transaction."""
        self.client.login(username='support', password='supportpass')
        response = self.client.post(reverse('validate_transaction_by_support', args=[self.support_request.id]))
        self.assertEqual(response.status_code, 200)
        self.support_request.refresh_from_db()
        self.assertEqual(self.support_request.transaction.status, 'completed')

    def test_archiving_chat(self):
        """Ensure the chat can be archived after support intervention."""
        self.client.login(username='support', password='supportpass')
        response = self.client.post(reverse('archive_chat', args=[self.support_request.id]))
        self.assertEqual(response.status_code, 200)
        # Check that the chat has been archived
        self.assertTrue(self.support_request.chatararchive_set.exists())
