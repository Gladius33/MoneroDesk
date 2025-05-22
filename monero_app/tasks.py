from celery import shared_task
from .services import MoneroService
import logging

logger = logging.getLogger(__name__)

@shared_task
def fetch_monero_rates():
    try:
        monero_service = MoneroService()
        monero_service.fetch_rates()
        logger.info("Monero rates updated successfully.")
    except Exception as e:
        logger.exception("Error updating Monero rates")

@shared_task
def monitor_transactions(account_index=0):
    try:
        monero_service = MoneroService()
        results = monero_service.monitor_transactions(account_index=account_index)
        logger.info(f"Monero transactions monitored successfully: {results}")
        # Si tu veux loguer dans un fichier séparé :
        # with open('/home/appuser/web/monerodesk.org/logs/monero_tasks.log', 'a') as f:
        #     f.write(f"Monitor tx results: {results}\n")
    except Exception as e:
        logger.exception("Error monitoring Monero transactions")

@shared_task
def check_or_create_main_wallet():
    """
    Task to check if the main wallet exists and create it if necessary.
    """
    try:
        monero_service = MoneroService()
        monero_service.check_or_create_main_wallet()
        logger.info("Main Monero wallet checked and created if necessary.")
    except Exception as e:
        logger.exception("Error in check_or_create_main_wallet")

