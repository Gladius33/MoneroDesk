from django.db import models
from django.contrib.auth.models import User
from monero_app.services import MoneroService
from accounts.models import Profile
from decimal import Decimal
from django.core.exceptions import ValidationError
from monero_app.models import MoneroRate


class Ad(models.Model):
    TYPE_CHOICES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]
    
    CRYPTO_CHOICES = [
        ('XMR', 'Monero'),
    ]
    
    FIAT_CHOICES = [
        ('EUR', 'Euro'),
        ('USD', 'US Dollar'),
        ('CHF', 'Swiss Franc'),
        ('RUB', 'Russian Ruble'),
        ('CAD', 'Canadian Dollar'),
        ('CNY', 'Chinese Yuan'),
    ]
    
    PAYMENT_CHOICES = [
        ('SEPA', 'SEPA'),
        ('INSTANT SEPA', 'Instant SEPA'),
        ('BANK TRANSFER', 'Bank Transfer'),
        ('DEBIT CARD', 'Debit Card'),
        ('VISA/MASTERCARD', 'Visa/MasterCard'),
        ('MIR', 'MIR'),
        ('PAYPAL', 'PayPal'),
        ('REVOLUT', 'Revolut'),
        ('ALIPAY', 'Alipay'),
        ('LYDIA', 'Lydia'),
        ('WECHAT', 'WeChat'),
        ('GIFT CARD', 'Gift Card'),
        ('CASH BY MAIL', 'Cash by Mail'),
        ('CASH IN HAND', 'Cash in Hand'),
        ('BTC', 'Bitcoin'),
        ('CRYPTOCURRENCY', 'Cryptocurrency'),
        ('GOODS', 'Goods'),
        ('OTHER', 'Other'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=4, choices=TYPE_CHOICES, default='sell')
    crypto_currency = models.CharField(max_length=3, choices=CRYPTO_CHOICES, default='XMR')
    fiat_currency = models.CharField(max_length=3, choices=FIAT_CHOICES, default='USD')
    price = models.DecimalField(max_digits=20, decimal_places=8, default=2)
    min_amount = models.DecimalField(max_digits=20, decimal_places=2, default=10)
    max_amount = models.DecimalField(max_digits=20, decimal_places=2, default=1000)
    payment_methods = models.CharField(max_length=255, choices=PAYMENT_CHOICES, default='BANK TRANSFER')
    payment_details = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True, default='Anywhere')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    escrow_wallet_address = models.CharField(max_length=255, blank=True, null=True)
    escrow_balance = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    dynamic_price = models.BooleanField(default=False)
    dynamic_price_value = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Percentage adjustment (-15% to 15%)")

    def __str__(self):
        return f"{self.title} - {self.type.capitalize()} {self.crypto_currency} - {self.user.username}"

    def create_escrow_wallet(self):
        if self.type == 'sell':
            monero_service = MoneroService()
            escrow_subaddress = monero_service.create_escrow_subaddress(label="Ad_Escrow_" + str(self.id))
            self.escrow_wallet_address = escrow_subaddress['address']
            self.save()

    def update_escrow_balance(self, amount):
        self.escrow_balance += amount
        self.save()

    def release_escrow_on_deletion(self):
        if self.escrow_balance > 0:
            monero_service = MoneroService()
            monero_service.return_funds_to_user(wallet_address=self.escrow_wallet_address, amount=self.escrow_balance)
            self.escrow_balance = 0
            self.save()

    def release_escrow_on_transaction_completion(self, transaction_amount):
        if self.escrow_balance >= transaction_amount:
            monero_service = MoneroService()
            monero_service.release_funds(wallet_address=self.escrow_wallet_address, amount=transaction_amount)
            self.escrow_balance -= transaction_amount
            self.save()

    def adjust_max_amount_and_active_status(self, transaction_amount):
        self.max_amount -= transaction_amount
        if self.max_amount <= 0 or (self.max_amount * self.price < Decimal(10)):
            self.active = False
        self.save()

    def revert_max_amount_on_transaction_cancel(self, transaction_amount):
        self.max_amount += transaction_amount
        self.active = True
        self.save()

    def clean(self):
        if self.payment_methods in ['GOODS', 'OTHER'] and not self.payment_details:
            raise ValidationError(f"Please provide additional details for the payment method '{self.payment_methods}'.")

    def update_dynamic_price(self):
        """
        Updates the price based on the Monero rate and the dynamic price percentage.
        This function should be called in a scheduled task.
        """
        if self.dynamic_price:
            monero_rate = MoneroRate.objects.get(currency=self.fiat_currency)
            adjustment = monero_rate.rate * (self.dynamic_price_value / 100)
            self.price = monero_rate.rate + adjustment
            self.save()

