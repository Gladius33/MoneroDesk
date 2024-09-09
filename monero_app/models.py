from django.db import models
from Crypto.Cipher import AES
from django.conf import settings
from decimal import Decimal

class EncryptedField(models.CharField):
    """
    Field to encrypt data before storing it in the database.
    """
    def get_db_prep_value(self, value, connection, prepared=False):
        if value:
            cipher = AES.new(settings.MONERO_APP_SECRET_KEY.encode('utf-8'), AES.MODE_EAX)
            ciphertext, tag = cipher.encrypt_and_digest(value.encode('utf-8'))
            return cipher.nonce.hex() + tag.hex() + ciphertext.hex()
        return value

    def from_db_value(self, value, expression, connection):
        if value:
            try:
                nonce = bytes.fromhex(value[:32])
                tag = bytes.fromhex(value[32:64])
                ciphertext = bytes.fromhex(value[64:])
                cipher = AES.new(settings.MONERO_APP_SECRET_KEY.encode('utf-8'), AES.MODE_EAX, nonce=nonce)
                return cipher.decrypt_and_verify(ciphertext, tag).decode('utf-8')
            except Exception as e:
                # Handle decryption errors gracefully
                print(f"Decryption failed: {e}")
                return None
        return value

class XmrWallet(models.Model):
    """
    Represents the main Monero wallet of the project.
    """
    address = EncryptedField(max_length=95, unique=True)
    balance = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.0'))
    wallet_type = models.CharField(max_length=10, choices=[('main', 'Main'), ('fee', 'Fee')], default='main')
    wallet_path = models.CharField(max_length=255, blank=True, null=True)  # Store wallet file path

    def __str__(self):
        return f"Wallet ({self.wallet_type}) - {self.address}"

class XmrSubaddress(models.Model):
    """
    Subaddresses derived from the main Monero wallet.
    """
    address = EncryptedField(max_length=95, unique=True)
    wallet_type = models.CharField(max_length=10, choices=[('user', 'User'), ('fee', 'Fee'), ('escrow', 'Escrow')])
    label = models.CharField(max_length=255, blank=True, null=True)  # Optional label for metadata (like transaction ID)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Subaddress ({self.wallet_type}) - {self.address}"

class MoneroTransaction(models.Model):
    """
    Monero internal and external transaction management.
    """
    tx_hash = EncryptedField(max_length=95, unique=True)
    wallet = models.ForeignKey(XmrWallet, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('failed', 'Failed')])
    confirmations = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    is_outgoing = models.BooleanField(default=False)  # To track if the transaction is outgoing or incoming
    destination_address = models.CharField(max_length=95, blank=True, null=True)  # For outgoing transactions

    def __str__(self):
        return f"Transaction {self.tx_hash} - {self.status}"

class MoneroRate(models.Model):
    """
    Monero exchange rates for fiat currencies.
    """
    currency = models.CharField(max_length=3, unique=True)
    rate = models.DecimalField(max_digits=20, decimal_places=8)
    inverse_rate = models.DecimalField(max_digits=20, decimal_places=8)
    last_updated = models.DateTimeField(auto_now=True)
    source = models.CharField(max_length=255, blank=True, null=True)  # To track the API provider (e.g., CoinMarketCap)

    def __str__(self):
        return f"1 XMR = {self.rate} {self.currency}"

