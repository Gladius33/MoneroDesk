from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from cryptography.fernet import Fernet  # Use to encrypt keys in the database

class Message(models.Model):
    from transactions.models import Transaction
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(blank=True)  # Can be blank if a file is uploaded
    encrypted = models.BooleanField(default=True)  # Indicates if the message is encrypted
    file = models.FileField(upload_to='chat_files/', blank=True, null=True)  # Optional file attachment
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'Message from {self.sender.username} in Transaction {self.transaction.id}'

    def get_created_at_utc(self):
        return self.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')

    def clean(self):
        # Example: Validate that text or file is provided
        if not self.text and not self.file:
            raise ValidationError('A message must contain either text or a file.')

class ChatEncryptionKey(models.Model):
    from transactions.models import Transaction
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='encryption_key')
    buyer_key = models.CharField(max_length=64)
    seller_key = models.CharField(max_length=64)

    def save(self, *args, **kwargs):
        # Encrypt the keys before saving
        cipher = Fernet(settings.ENCRYPTION_KEY)
        self.buyer_key = cipher.encrypt(self.buyer_key.encode()).decode()
        self.seller_key = cipher.encrypt(self.seller_key.encode()).decode()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Encryption Key for Transaction {self.transaction.id}'
