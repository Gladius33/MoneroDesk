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
import logging

# Allowed formats and file size
ALLOWED_FILE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/jpg', 'application/pdf']
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB

# Set up logging for the consumer
logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        Connect the WebSocket to the appropriate chat room based on the transaction.
        """
        self.transaction_id = self.scope['url_route']['kwargs']['transaction_pk']
        self.room_group_name = f'chat_{self.transaction_id}'

        # Join the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Notify if support has joined
        if self.scope["user"].is_staff or self.scope["user"].is_superuser:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'support_joined',
                    'message': 'Support has joined the chat.'
                }
            )

    async def disconnect(self, close_code):
        """
        Disconnect the WebSocket and remove from the room group.
        """
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # Notify if support has left
        if self.scope["user"].is_staff or self.scope["user"].is_superuser:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'support_left',
                    'message': 'Support has left the chat.'
                }
            )

    async def receive(self, text_data):
        """
        Receive a message or file, encrypt it, and broadcast it to the chat room.
        """
        text_data_json = json.loads(text_data)
        message_content = text_data_json.get('message')
        sender_user = self.scope["user"]

        # Fetch the transaction and encryption key
        transaction = get_object_or_404(Transaction, id=self.transaction_id)
        chat_key = get_object_or_404(ChatEncryptionKey, transaction=transaction)

        # Handle file uploads
        file = text_data_json.get('file')
        if file:
            encrypted_file = self.encrypt_file(file, chat_key, sender_user)
            Message.objects.create(
                transaction=transaction,
                sender=sender_user,
                text='',
                file=encrypted_file
            )

        # Handle text messages
        if message_content:
            encrypted_message = self.encrypt_message(message_content, chat_key, sender_user)
            Message.objects.create(
                transaction=transaction,
                sender=sender_user,
                text=encrypted_message
            )

        # Broadcast the message to the room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_content,
                'sender': sender_user.username
            }
        )

    async def chat_message(self, event):
        """
        Handle incoming messages and broadcast them to WebSocket clients.
        """
        message = event['message']
        sender = event['sender']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender
        }))

    async def support_joined(self, event):
        """
        Notify when support has joined the chat.
        """
        message = event['message']
        await self.send(text_data=json.dumps({
            'message': message,
            'event': 'support_joined'
        }))

    async def support_left(self, event):
        """
        Notify when support has left the chat.
        """
        message = event['message']
        await self.send(text_data=json.dumps({
            'message': message,
            'event': 'support_left'
        }))

    def encrypt_message(self, message, chat_key, user):
        """
        Encrypt a text message using AES encryption.
        """
        key = self.get_user_chat_key(chat_key, user)
        cipher = AES.new(base64.b64decode(key), AES.MODE_EAX)
        nonce = cipher.nonce
        ciphertext, tag = cipher.encrypt_and_digest(message.encode('utf-8'))
        return base64.b64encode(nonce + tag + ciphertext).decode('utf-8')

    def encrypt_file(self, file, chat_key, user):
        """
        Encrypt an uploaded file using AES encryption.
        """
        self.validate_file(file)
        key = self.get_user_chat_key(chat_key, user)
        cipher = AES.new(base64.b64decode(key), AES.MODE_EAX)
        nonce = cipher.nonce
        file_data = file.read()
        ciphertext, tag = cipher.encrypt_and_digest(file_data)
        return base64.b64encode(nonce + tag + ciphertext)

    def validate_file(self, file: UploadedFile):
        """
        Validate the file's size and type before processing.
        """
        if file.size > MAX_FILE_SIZE:
            raise ValidationError(f"File size exceeds the maximum limit of {MAX_FILE_SIZE // (1024 * 1024)} MB.")

        file_type, _ = guess_type(file.name)
        if file_type not in ALLOWED_FILE_TYPES:
            raise ValidationError(f"Invalid file type: {file_type}. Allowed types: {', '.join(ALLOWED_FILE_TYPES)}")

    def get_user_chat_key(self, chat_key, user):
        """
        Retrieve the encryption key for the buyer, seller, or support.
        """
        if user == chat_key.transaction.buyer:
            return chat_key.buyer_key
        elif user == chat_key.transaction.seller:
            return chat_key.seller_key
        elif user.is_staff or user.is_superuser:
            return chat_key.buyer_key  # Support uses buyer key by default
        else:
            raise ValueError("User does not have access to the chat encryption key.")
