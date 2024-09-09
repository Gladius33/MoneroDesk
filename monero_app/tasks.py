from celery import shared_task
from .services import MoneroService
from .models import MoneroRate
from django.utils.timezone import now
import logging

logger = logging.getLogger(__name__)

@shared_task
def fetch_monero_rates():
    monero_service = MoneroService()
    rates = monero_service.fetch_rates()
    for currency, rate_data in rates.items():
        MoneroRate.objects.update_or_create(
            currency=currency,
            defaults={'rate': rate_data['rate'], 'inverse_rate': rate_data['inverse_rate'], 'last_updated': now()}
        )
    logger.info("Monero rates updated successfully.")

@shared_task
def monitor_transactions():
    monero_service = MoneroService()
    monero_service.monitor_all_transactions()
    logger.info("Monero transactions monitored successfully.")
