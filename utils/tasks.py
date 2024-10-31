import requests
from django.utils import timezone
from .models import ExchangeRate

def update_exchange_rates():
    response = requests.get('https://api.coingecko.com/api/v3/exchange_rates')
    rates = response.json().get('rates', {})

    for currency, data in rates.items():
        rate, created = ExchangeRate.objects.get_or_create(currency=currency)
        rate.rate = data.get('value')
        rate.last_updated = timezone.now()
        rate.save()
