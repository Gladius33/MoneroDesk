from django.db import models
from transactions.models import Transaction
from django.contrib.auth.models import User
from Crypto.Cipher import AES
import base64
from decouple import config

class SupportRequest(models.Model):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE)
    support_agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('waiting', 'Waiting'),
        ('in_room', 'In Room'),
        ('closed', 'Closed')
    ], default='waiting')
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    action_taken = models.CharField(max_length=50, choices=[
        ('canceled', 'Transaction Canceled'),
        ('validated', 'Escrow Released'),
        ('no_action', 'No Action Taken')
    ], default='no_action')
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Support Request for Transaction {self.transaction.id}"


class ChatArchive(models.Model):
    support_request = models.ForeignKey(SupportRequest, on_delete=models.CASCADE)
    chat_data = models.TextField()  # Chiffré
    archived_at = models.DateTimeField(auto_now_add=True)

    def encrypt_data(self, data):
        key = base64.b64decode(config('SUPPORT_AES_KEY'))
        cipher = AES.new(key, AES.MODE_EAX)
        nonce = cipher.nonce
        ciphertext, tag = cipher.encrypt_and_digest(data.encode('utf-8'))
        return base64.b64encode(nonce + tag + ciphertext).decode('utf-8')

    def decrypt_data(self, encrypted_data):
        key = base64.b64decode(config('SUPPORT_AES_KEY'))
        data = base64.b64decode(encrypted_data)
        nonce, tag, ciphertext = data[:16], data[16:32], data[32:]
        cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
        return cipher.decrypt_and_verify(ciphertext, tag).decode('utf-8')

    def save(self, *args, **kwargs):
        # Avant de sauvegarder, on chiffre les données
        self.chat_data = self.encrypt_data(self.chat_data)
        super().save(*args, **kwargs)

    def get_chat(self):
        # Déchiffrement des données
        return self.decrypt_data(self.chat_data)
