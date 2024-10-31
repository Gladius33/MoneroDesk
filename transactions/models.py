from django.db import models
from django.contrib.auth.models import User
from ads.models import Ad
from django.utils import timezone
from monero_app.services import MoneroService
from decimal import Decimal
import secrets


# AutoRefundUserList Model
class AutoRefundUserList(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    auto_refund_enabled = models.BooleanField(default=False)

    def __str__(self):
        return f"AutoRefundUserList for {self.user.username}"


class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]

    buyer = models.ForeignKey(User, related_name='buyer', on_delete=models.CASCADE)
    seller = models.ForeignKey(User, related_name='seller', on_delete=models.CASCADE)
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE)
    transaction_amount = models.DecimalField(max_digits=20, decimal_places=8)  # Amount of the transaction
    price = models.DecimalField(max_digits=20, decimal_places=8)  # Price of Monero in fiat currency
    fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('1.0'))  # Default 1% fee
    fiat_currency = models.CharField(max_length=3, choices=[
        ('USD', 'USD'), ('EUR', 'EUR'), ('CHF', 'CHF'), ('RUB', 'RUB'), ('CAD', 'CAD'), ('CNY', 'CNY')
    ])
    payment_methods = models.CharField(max_length=255)
    escrow_wallet_address = models.CharField(max_length=255, blank=True, null=True)  # Escrow address
    escrow_released = models.BooleanField(default=False)
    payment_sent = models.BooleanField(default=False)  # Track when buyer marks payment as sent
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')  # Status of the transaction
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=timezone.now() + timezone.timedelta(hours=1, minutes=30))
    transaction_id = models.CharField(max_length=255, unique=True, blank=True, null=True)

    @classmethod
    def create_sell_transaction(cls, buyer, ad, transaction_amount):
        """
        Creates a sell transaction where the buyer purchases XMR from the seller (ad owner).
        """
        if ad.type == 'sell':
            if transaction_amount < ad.min_amount or transaction_amount > ad.max_amount:
                raise ValueError("Transaction amount is outside the allowed range.")

            if not ad.escrow_wallet_address:
                raise ValueError("Escrow address not found for this ad.")

            transaction = cls.objects.create(
                buyer=buyer,
                seller=ad.user,
                ad=ad,
                transaction_amount=transaction_amount,
                price=ad.price,
                fiat_currency=ad.fiat_currency,
                payment_methods=ad.payment_methods,
                escrow_wallet_address=ad.escrow_wallet_address
            )
            
            monero_service = MoneroService()
            monero_service.send_xmr(to_address=ad.escrow_wallet_address, amount=transaction_amount, escrow=True)
            
            ad.max_amount -= transaction_amount
            if ad.max_amount <= 0 or ad.max_amount * ad.price < Decimal(10):
                ad.active = False
            ad.save()
            
            return transaction

    @classmethod
    def create_buy_transaction(cls, seller, ad, transaction_amount):
        """
        Creates a buy transaction where the seller sends XMR to the buyer.
        """
        if ad.type == 'buy':
            if transaction_amount < ad.min_amount or transaction_amount > ad.max_amount:
                raise ValueError("Transaction amount is outside the allowed range.")

            transaction = cls.objects.create(
                buyer=ad.user,
                seller=seller,
                ad=ad,
                transaction_amount=transaction_amount,
                price=ad.price,
                fiat_currency=ad.fiat_currency,
                payment_methods=ad.payment_methods
            )

            monero_service = MoneroService()
            escrow_address = monero_service.create_escrow_subaddress(label=f"Escrow_Ad_{ad.id}")
            transaction.escrow_wallet_address = escrow_address['address']
            transaction.save()
            monero_service.send_xmr(to_address=escrow_address['address'], amount=transaction_amount, escrow=True)

            ad.max_amount -= transaction_amount
            if ad.max_amount <= 0 or ad.max_amount * ad.price < Decimal(10):
                ad.active = False
            ad.save()

            return transaction

    def release_escrow(self):
        """
        Releases funds from escrow to the buyer after the transaction is completed.
        """
        if not self.escrow_released and self.escrow_wallet_address:
            monero_service = MoneroService()
            escrow_amount = self.transaction_amount
            monero_service.send_xmr(to_address=self.buyer.profile.user_subaddress, amount=escrow_amount, escrow=True)
            self.escrow_released = True
            self.save()

    def cancel_transaction(self):
        """
        Cancels the transaction and returns the escrow funds to the seller (for type 'buy').
        For type 'sell', only the ad's max_amount is updated.
        """
        monero_service = MoneroService()
        if self.ad.type == 'buy' and self.escrow_wallet_address:
            monero_service.send_xmr(to_address=self.seller.profile.user_subaddress, amount=self.transaction_amount, escrow=True)
        
        self.ad.max_amount += self.transaction_amount
        self.ad.active = True
        self.ad.save()
        self.delete()

    def confirm_transaction(self):
        """
        Confirms the transaction and releases funds from escrow.
        """
        if not self.escrow_released:
            monero_service = MoneroService()
            net_amount = self.apply_fee(self.transaction_amount, self.fee_percentage)
            fee_amount = self.transaction_amount - net_amount

            monero_service.send_xmr(to_address=self.buyer.profile.user_subaddress, amount=net_amount, escrow=True)

            fee_subaddress = monero_service.create_fee_subaddress(label=f"Fee_{self.transaction_id}")
            monero_service.send_xmr(to_address=fee_subaddress['address'], amount=fee_amount, fee=True)

            self.escrow_released = True
            self.save()

    def create_chatroom(self):
        from chat.models import ChatEncryptionKey
        buyer_key = secrets.token_urlsafe(32)
        seller_key = secrets.token_urlsafe(32)

        ChatEncryptionKey.objects.create(
            transaction=self,
            buyer_key=buyer_key,
            seller_key=seller_key
        )

    def save(self, *args, **kwargs):
        from chat.models import ChatEncryptionKey
        if not self.transaction_id:
            self.transaction_id = secrets.token_urlsafe(12)
        super().save(*args, **kwargs)

        if not ChatEncryptionKey.objects.filter(transaction=self).exists():
            self.create_chatroom()

    def __str__(self):
        return f'Transaction {self.transaction_id} between {self.buyer.username} and {self.seller.username}'
