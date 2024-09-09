import os
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from monero_app.services import MoneroService


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
        monero_service = MoneroService()
        balance_data = monero_service.get_subaddress_balance_and_transactions(self.user_subaddress)
        self.xmr_balance = balance_data['balance']
        self.save()
        return balance_data


    # Gérer le retrait de Monero avec les frais
    def withdraw_monero(self, amount, withdraw_address, fee_percentage):
        """
        Effectue un retrait de Monero depuis le portefeuille de l'utilisateur avec calcul des frais.
        """
        if self.xmr_balance >= amount:
            fees = amount * (fee_percentage / 100)
            net_amount = amount - fees
            
            # Initialiser le portefeuille Monero à partir de l'adresse de l'utilisateur
            wallet = MoneroWallet(self.xmr_wallet_address)
            
            # Effectuer le transfert Monero
            tx_hash = wallet.transfer([{'address': withdraw_address, 'amount': net_amount}], priority=2)
            
            # Mise à jour du solde
            self.xmr_balance -= amount
            self.save()
            
            return tx_hash
        else:
            raise ValueError("Insufficient balance for withdrawal.")

