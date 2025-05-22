import requests
from django.conf import settings
from django.utils import timezone
from .models import ExchangeRate

def update_exchange_rates():
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    headers = {'X-CMC_PRO_API_KEY': settings.X_CMC_PRO_API_KEY}
    # Adapte la liste des FIAT ici si besoin
    params = {'symbol': 'XMR', 'convert': 'USD,BTC,EUR,CHF,RUB,CAD,CNY'}

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    rates = data['data']['XMR']['quote']

    for currency, rate_data in rates.items():
        rate_obj, created = ExchangeRate.objects.get_or_create(currency=currency)
        rate_obj.rate = rate_data['price']
        rate_obj.last_updated = timezone.now()
        rate_obj.save()

