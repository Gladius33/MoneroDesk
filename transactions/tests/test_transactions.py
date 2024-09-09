from django.test import TestCase
from django.urls import reverse
from models import Transaction

class TestTransactions(TestCase):

    def setUp(self):
        # Set up initial data
        pass

    def test_create_transaction(self):
        # Test transaction creation
        response = self.client.post(reverse('create_transaction'), {
            'ad_id': 1,
            'amount': 10,
        })
        self.assertEqual(response.status_code, 200)

    def test_escrow_management(self):
        # Test escrow wallet interaction
        transaction = Transaction.objects.create(amount=10, status='pending')
        transaction.lock_funds()  # Move funds to escrow
        self.assertEqual(transaction.status, 'escrow')

    def test_release_funds(self):
        # Test release of funds to buyer
        transaction = Transaction.objects.create(amount=10, status='escrow')
        transaction.release_funds()
        self.assertEqual(transaction.status, 'completed')

    def test_cancel_transaction(self):
        # Test canceling a transaction
        transaction = Transaction.objects.create(amount=10, status='pending')
        transaction.cancel_transaction()
        self.assertEqual(transaction.status, 'canceled')
