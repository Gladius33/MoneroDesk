from django.test import TestCase
from django.urls import reverse
from models import Ad

class TestAds(TestCase):
    
    def setUp(self):
        # Set up initial data
        pass

    def test_create_sell_ad(self):
        # Test creating a sell ad
        response = self.client.post(reverse('create_ad'), {
            'ad_type': 'sell',
            'price': 100,
            'currency': 'USD',
            'percentage': 10  # selling 10% above market price
        })
        self.assertEqual(response.status_code, 200)

    def test_create_buy_ad(self):
        # Test creating a buy ad
        response = self.client.post(reverse('create_ad'), {
            'ad_type': 'buy',
            'price': 50,
            'currency': 'USD',
            'percentage': -5  # buying 5% below market price
        })
        self.assertEqual(response.status_code, 200)

    def test_price_adjustment(self):
        # Test automatic price adjustment based on percentage
        ad = Ad.objects.create(ad_type='sell', price=100, percentage=10, currency='USD')
        adjusted_price = ad.calculate_market_price()
        self.assertEqual(adjusted_price, 110)  # 10% above base price
