from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class AdminSettings(models.Model):
    fee_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=1.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    withdraw_fee_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.5,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    xmr_wallet_address = models.CharField(max_length=255)
    referral_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.5,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    def __str__(self):
        return "Admin Settings"

    @classmethod
    def get_referral_percentage(cls):
        settings, created = cls.objects.get_or_create(id=1)
        return settings.referral_percentage

    @classmethod
    def set_referral_percentage(cls, new_percentage):
        settings, created = cls.objects.get_or_create(id=1)
        settings.referral_percentage = new_percentage
        settings.save()

