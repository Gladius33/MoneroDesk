from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from monero_app.services import MoneroService
from decimal import Decimal
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

class User(AbstractUser):
    groups = models.ManyToManyField(
        Group,
        related_name='custom_user_groups',
        blank=True,
        help_text=('The groups this user belongs to. A user will get all permissions granted to each of their groups.'),
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_user_permissions',
        blank=True,
        help_text=('Specific permissions for this user.'),
        related_query_name='custom_user_permission',
    )
    
    def __str__(self):
        return self.username


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    user_subaddress = models.CharField(max_length=255, blank=False, null=False)  # Monero subaddress
    xmr_balance = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    referral_code = models.CharField(max_length=20, unique=True, null=True, blank=True)  # Referral code
    referred_users = models.ManyToManyField(User, related_name='referrals', blank=True)  # Referrals
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} Profile'

    def update_balance_and_transactions(self):
        """
        Met à jour le solde Monero et récupère les transactions pour le sous-adresse de l'utilisateur.
        """
        monero_service = MoneroService()
        try:
            balance_data = monero_service.get_subaddress_balance_and_transactions(self.user_subaddress)
            if balance_data:
                self.xmr_balance = balance_data['balance']
                self.save()
                logger.info(f"Balance and transactions updated for {self.user.username}.")
                return balance_data
            else:
                logger.warning(f"Failed to fetch balance data for {self.user.username}.")
                raise ValueError("Unable to fetch balance data from Monero service.")
        except Exception as e:
            logger.error(f"Error fetching balance and transactions for {self.user.username}: {e}")
            raise ValueError(f"Error fetching balance and transactions: {e}")

    def withdraw_monero(self, amount, withdraw_address, fee_percentage):
        """
        Effectue un retrait de Monero avec les frais et met à jour le solde.
        """
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")
        if self.xmr_balance < amount:
            raise ValueError("Insufficient balance for withdrawal.")

        fees = amount * (fee_percentage / 100)
        net_amount = amount - fees
        if net_amount <= 0:
            raise ValueError("The amount after fees must be greater than zero.")

        # Utilisation de Celery pour effectuer le retrait de manière asynchrone
        process_withdrawal_task.delay(self.id, withdraw_address, net_amount, amount, fees)


# Définir la tâche Celery en dehors de la classe Profile
@shared_task
def process_withdrawal_task(profile_id, withdraw_address, net_amount, total_amount, fees):
    """
    Tâche asynchrone pour traiter le retrait Monero.
    """
    try:
        profile = Profile.objects.get(id=profile_id)
        monero_service = MoneroService()

        # Effectuer la transaction Monero avec le service MoneroService
        tx_hash = monero_service.send_xmr(withdraw_address, net_amount)
        if tx_hash:
            profile.xmr_balance -= total_amount  # Réduire le montant total du solde
            profile.save()
            logger.info(f"Withdrawal of {net_amount} XMR successful for {profile.user.username}. TX Hash: {tx_hash}")
        else:
            logger.warning(f"Transaction failed for {profile.user.username}.")
            raise ValueError("Transaction failed.")
    except Exception as e:
        logger.error(f"Error processing Monero withdrawal for profile {profile_id}: {e}")
        raise ValueError(f"Error processing the Monero transaction: {e}")
