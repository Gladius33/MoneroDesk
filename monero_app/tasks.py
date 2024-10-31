from celery import shared_task
from .services import MoneroService
from .models import MoneroRate
from django.utils.timezone import now
import logging

logger = logging.getLogger(__name__)

@shared_task
def fetch_monero_rates():
    """
    Task to fetch the latest Monero exchange rates and update them in the database.
    """
    monero_service = MoneroService()
    rates = monero_service.fetch_rates()
    if rates:
        for currency, rate_data in rates.items():
            MoneroRate.objects.update_or_create(
                currency=currency,
                defaults={
                    'rate': rate_data['rate'],
                    'inverse_rate': rate_data['inverse_rate'],
                    'last_updated': now()
                }
            )
        logger.info("Monero rates updated successfully.")
    else:
        logger.error("Failed to fetch Monero rates.")

@shared_task
def monitor_transactions():
    """
    Task to monitor all transactions to update their statuses.
    """
    monero_service = MoneroService()
    monero_service.monitor_all_transactions()
    logger.info("Monero transactions monitored successfully.")

@shared_task
def check_or_create_main_wallet():
    """
    Task to check if the main wallet exists and create it if necessary.
    """
    monero_service = MoneroService()
    monero_service.check_or_create_main_wallet()
    logger.info("Main Monero wallet checked and created if necessary.")
