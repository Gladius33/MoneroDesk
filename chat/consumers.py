import json
import base64
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Message, ChatEncryptionKey
from transactions.models import Transaction
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from Crypto.Cipher import AES
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from mimetypes import guess_type

# Formats autorisés
ALLOWED_FILE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/jpg', 'application/pdf']
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 Mo

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.transaction_id = self.scope['url_route']['kwargs']['transaction_pk']
        self.room_group_name = f'chat_{self.transaction_id}'

        # Rejoindre le groupe de la salle
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Notifier les participants si le support rejoint le chat
        if self.scope["user"].is_staff or self.scope["user"].is_superuser:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'support_joined',
                    'message': 'Support has joined the chat.'
                }
            )

    async def disconnect(self, close_code):
        # Quitter le groupe de la salle
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # Notifier les participants si le support quitte le chat
        if self.scope["user"].is_staff or self.scope["user"].is_superuser:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'support_left',
                    'message': 'Support has left the chat.'
                }
            )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json.get('message')
        sender_user = self.scope["user"]

        # Récupérer la transaction liée
        transaction = get_object_or_404(Transaction, id=self.transaction_id)

        # Récupérer la clé de chiffrement pour la transaction
        chat_key = get_object_or_404(ChatEncryptionKey, transaction=transaction)

        # Si c'est un fichier qui est envoyé, gérer l'envoi de fichier
        file = text_data_json.get('file')
        if file:
            encrypted_file = self.encrypt_file(file, chat_key, sender_user)
            # Valider et enregistrer le fichier crypté
            Message.objects.create(
                transaction=transaction,
                sender=sender_user,
                text='',
                file=encrypted_file
            )

        # Si c'est un message texte, le gérer
        if message_content:
            encrypted_message = self.encrypt_message(message_content, chat_key, sender_user)
            # Enregistrer le message dans la base de données (crypté)
            Message.objects.create(
                transaction=transaction,
                sender=sender_user,
                text=encrypted_message
            )

        # Envoyer le message au groupe de la salle (texte brut pour l'affichage immédiat)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_content,  # Message en texte brut pour les autres
                'sender': sender_user.username
            }
        )

    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']

        # Envoyer le message au WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender
        }))

    async def support_joined(self, event):
        message = event['message']

        # Notifier que le support a rejoint
        await self.send(text_data=json.dumps({
            'message': message,
            'event': 'support_joined'
        }))

    async def support_left(self, event):
        message = event['message']

        # Notifier que le support a quitté
        await self.send(text_data=json.dumps({
            'message': message,
            'event': 'support_left'
        }))

    def encrypt_message(self, message, chat_key, user):
        """
        Fonction pour chiffrer un message avec la clé de chat fournie.
        """
        key = self.get_user_chat_key(chat_key, user)
        cipher = AES.new(base64.b64decode(key), AES.MODE_EAX)
        nonce = cipher.nonce
        ciphertext, tag = cipher.encrypt_and_digest(message.encode('utf-8'))
        return base64.b64encode(nonce + tag + ciphertext).decode('utf-8')

    def encrypt_file(self, file, chat_key, user):
        """
        Fonction pour chiffrer un fichier avant de l'envoyer via WebSocket.
        """
        self.validate_file(file)
        key = self.get_user_chat_key(chat_key, user)
        cipher = AES.new(base64.b64decode(key), AES.MODE_EAX)
        nonce = cipher.nonce
        file_data = file.read()
        ciphertext, tag = cipher.encrypt_and_digest(file_data)
        return base64.b64encode(nonce + tag + ciphertext)

    def validate_file(self, file: UploadedFile):
        """Valide la taille et le type du fichier."""
        if file.size > MAX_FILE_SIZE:
            raise ValidationError("La taille du fichier dépasse la limite de 15 Mo.")
        
        # Vérification du type MIME basé sur le contenu
        file_type, _ = guess_type(file.name)
        if file_type not in ALLOWED_FILE_TYPES:
            raise ValidationError(f"Type de fichier invalide : {file_type}. Seules les images et PDF sont autorisés.")
        
        # Validation du type MIME en inspectant le contenu réel du fichier
        if not self.is_valid_mime_type(file, file_type):
            raise ValidationError("Le contenu du fichier ne correspond pas à son extension. Upload rejeté.")

    def is_valid_mime_type(self, file: UploadedFile, mime_type: str):
        """Vérifie que le type MIME du fichier correspond au contenu réel."""
        try:
            if 'image' in mime_type:
                from PIL import Image
                img = Image.open(file)
                img.verify()  # Vérifie que c'est une image valide
            elif mime_type == 'application/pdf':
                file.seek(0)
                return file.read(4) == b'%PDF'
            return True
        except Exception:
            return False

    def get_user_chat_key(self, chat_key, user):
        """
        Fonction pour récupérer la clé de chat de l'utilisateur (acheteur, vendeur, ou support).
        """
        if user == chat_key.transaction.buyer:
            return chat_key.buyer_key
        elif user == chat_key.transaction.seller:
            return chat_key.seller_key
        elif user.is_staff or user.is_superuser:
            # Utilise une clé partagée pour le support (ou clé du buyer selon la logique)
            return chat_key.buyer_key
        else:
            raise ValueError("L'utilisateur n'a pas accès à cette clé de chiffrement.")
