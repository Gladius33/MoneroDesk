from django.db import models
from django.contrib.auth.models import User
from transactions.models import Transaction
from django.utils import timezone

class Message(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(blank=True)  # Le texte peut être vide si un fichier est envoyé
    encrypted = models.BooleanField(default=True)  # Indique si le message est chiffré
    file = models.FileField(upload_to='chat_files/', blank=True, null=True)  # Fichiers joints (images, pdf, etc.)
    created_at = models.DateTimeField(default=timezone.now)  # Horodatage en UTC au moment de la création

    def __str__(self):
        return f'Message from {self.sender.username} in Transaction {self.transaction.id}'

    def get_created_at_utc(self):
        """
        Retourne l'horodatage UTC formaté pour l'affichage à l'utilisateur.
        """
        return self.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')


class ChatEncryptionKey(models.Model):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='encryption_key')
    buyer_key = models.CharField(max_length=64)
    seller_key = models.CharField(max_length=64)

    def __str__(self):
        return f'Encryption Key for Transaction {self.transaction.id}'

