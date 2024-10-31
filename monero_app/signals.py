from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import XmrSubaddress, MoneroRate
from accounts.models import Profile
from .services import MoneroService
import logging
from transactions.models import Transaction
from ads.models import Ad

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Profile)
def create_user_subaddress(sender, instance, created, **kwargs):
    """
    Signal to create a Monero subaddress for a user when a new Profile is created.
    """
    if created:
        try:
            monero_service = MoneroService()
            subaddress = monero_service.create_user_subaddress(label=instance.user.username)
            
            if subaddress:
                XmrSubaddress.objects.create(
                    user=instance.user, 
                    address=subaddress['address'], 
                    wallet_type='user'
                )
                logger.info(f"Monero user subaddress created for {instance.user.username}")
            else:
                logger.error(f"Failed to create user subaddress for {instance.user.username}")

        except Exception as e:
            logger.error(f"Error creating user subaddress for {instance.user.username}: {e}")

@receiver(post_save, sender=Ad)
def create_escrow_and_fee_subaddresses(sender, instance, created, **kwargs):
    """
    Signal to create escrow and fee subaddresses when an Ad is created for a sell transaction.
    """
    if created and instance.type == 'sell':
        try:
            monero_service = MoneroService()
            # Create escrow subaddress
            escrow_subaddress = monero_service.create_escrow_subaddress(label=f"Escrow_Ad_{instance.id}")
            if escrow_subaddress:
                instance.escrow_wallet_address = escrow_subaddress['address']
                instance.save()
                logger.info(f"Escrow subaddress created for Ad {instance.id}")

            # Create fee subaddress
            fee_subaddress = monero_service.create_fee_subaddress(label=f"Fee_Ad_{instance.id}")
            if fee_subaddress:
                logger.info(f"Fee subaddress created for Ad {instance.id}")
            else:
                logger.error(f"Failed to create fee subaddress for Ad {instance.id}")

        except Exception as e:
            logger.error(f"Error creating escrow or fee subaddress for Ad {instance.id}: {e}")

@receiver(post_save, sender=Transaction)
def handle_transaction(sender, instance, created, **kwargs):
    """
    Signal to handle Monero transfers when a transaction is completed.
    """
    if created and instance.status == 'completed':
        try:
            monero_service = MoneroService()
            # Transfer funds from escrow to buyer or seller depending on transaction type
            if instance.ad.type == 'sell':
                buyer_subaddress = instance.buyer.profile.user_subaddress
                monero_service.release_funds(instance.escrow_wallet_address, buyer_subaddress)
                logger.info(f"Released escrow funds for Transaction {instance.transaction_id} to buyer.")
            elif instance.ad.type == 'buy':
                seller_subaddress = instance.seller.profile.user_subaddress
                monero_service.release_funds(instance.escrow_wallet_address, seller_subaddress)
                logger.info(f"Released escrow funds for Transaction {instance.transaction_id} to seller.")

            # Transfer fees to the fee subaddress
            fee_amount = instance.transaction_amount * instance.fee_percentage / 100
            fee_subaddress = monero_service.create_fee_subaddress(label=f"Fee_Transaction_{instance.id}")
            if fee_subaddress:
                monero_service.send_xmr(fee_subaddress, fee_amount, fee=True)
                logger.info(f"Transferred fees for Transaction {instance.transaction_id} to fee subaddress.")
            else:
                logger.error(f"Failed to create fee subaddress for transaction {instance.transaction_id}.")

        except Exception as e:
            logger.error(f"Error handling transaction {instance.transaction_id}: {e}")
