from django.db import models

class AdminSettings(models.Model):
    fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)  # Fee for transactions (1% by default)
    withdraw_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.5)  # Fee for withdrawals
    xmr_wallet_address = models.CharField(max_length=255)

    def __str__(self):
        return "Admin Settings"
