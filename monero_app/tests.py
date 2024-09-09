from django.test import TestCase
from services import MoneroService

class MoneroServiceTests(TestCase):
    def test_create_wallet(self):
        monero_service = MoneroService()
        wallet = monero_service.check_or_create_main_wallet()
        self.assertIsNotNone(wallet)

    def test_create_user_subaddress(self):
        monero_service = MoneroService()
        subaddress = monero_service.create_user_subaddress(label='testuser')
        self.assertIsNotNone(subaddress)
