from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Message, ChatEncryptionKey
from transactions.models import Transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.exceptions import ValidationError
from mimetypes import guess_type
from django.contrib import messages
from django.core.files.uploadedfile import UploadedFile
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import logging
import json


# Allowed formats and file size
ALLOWED_FILE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/jpg', 'application/pdf']
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB

# Set up logging for the chat application
logger = logging.getLogger(__name__)

@login_required
def chat_room_view(request, transaction_pk):
    """
    Displays the chat room for a specific transaction and handles message/file submission.
    """
    transaction = get_object_or_404(Transaction, pk=transaction_pk)
    chat_key = get_object_or_404(ChatEncryptionKey, transaction=transaction)

    # Validate user access
    if not (request.user == transaction.buyer or request.user == transaction.seller or request.user.is_staff):
        messages.error(request, "You are not authorized to access this chat.")
        return redirect('some_other_view')

    if request.method == 'POST':
        text = request.POST.get('text')
        file = request.FILES.get('file')

        # Encrypt message if available
        encrypted_text = encrypt_message(text, chat_key, request.user) if text else None
        encrypted_file = encrypt_file(file, chat_key, request.user) if file else None

        # Save message or file
        if text or file:
            try:
                Message.objects.create(
                    transaction=transaction,
                    sender=request.user,
                    text=encrypted_text,
                    file=encrypted_file
                )
            except ValidationError as e:
                messages.error(request, f"Error: {e.message}")
                logger.error(f"Validation error while saving message: {e}")

    # Decrypt messages for display
    messages_list = decrypt_messages(transaction.messages.all(), chat_key, request.user)
    return render(request, 'chat/chat_room.html', {
        'transaction': transaction,
        'messages': messages_list
    })

def encrypt_message(message, chat_key, user):
    """
    Encrypts a message using AES encryption.
    """
    key = get_user_chat_key(chat_key, user)
    cipher = AES.new(base64.b64decode(key), AES.MODE_EAX)
    nonce = cipher.nonce
    ciphertext, tag = cipher.encrypt_and_digest(message.encode('utf-8'))
    return base64.b64encode(nonce + tag + ciphertext).decode('utf-8')

def decrypt_messages(messages, chat_key, user):
    """
    Decrypts all messages for a chat session.
    """
    decrypted_messages = []
    for message in messages:
        decrypted_text = decrypt_message(message.text, chat_key, user)
        decrypted_messages.append({
            'sender': message.sender,
            'text': decrypted_text,
            'file': message.file,
            'created_at': message.created_at
        })
    return decrypted_messages

def decrypt_message(encrypted_message, chat_key, user):
    """
    Decrypts an individual encrypted message.
    """
    key = get_user_chat_key(chat_key, user)
    data = base64.b64decode(encrypted_message)
    nonce, tag, ciphertext = data[:16], data[16:32], data[32:]
    cipher = AES.new(base64.b64decode(key), AES.MODE_EAX, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag).decode('utf-8')

def encrypt_file(file, chat_key, user):
    """
    Encrypts an uploaded file using AES encryption before storing it.
    """
    if file:
        validate_file(file)  # Validate file before encryption
        key = get_user_chat_key(chat_key, user)
        cipher = AES.new(base64.b64decode(key), AES.MODE_EAX)
        nonce = cipher.nonce
        file_data = file.read()
        ciphertext, tag = cipher.encrypt_and_digest(file_data)
        encrypted_file_data = base64.b64encode(nonce + tag + ciphertext)
        return encrypted_file_data

def validate_file(file: UploadedFile):
    """
    Validates the uploaded file's size and MIME type.
    """
    if file.size > MAX_FILE_SIZE:
        raise ValidationError(f"File size exceeds the maximum limit of {MAX_FILE_SIZE // (1024 * 1024)} MB.")
    
    file_type, _ = guess_type(file.name)
    if file_type not in ALLOWED_FILE_TYPES:
        raise ValidationError(f"Invalid file type: {file_type}. Allowed types: {', '.join(ALLOWED_FILE_TYPES)}")

def get_user_chat_key(chat_key, user):
    """
    Retrieves the appropriate encryption key for the user.
    """
    if user == chat_key.transaction.buyer:
        return chat_key.buyer_key
    elif user == chat_key.transaction.seller:
        return chat_key.seller_key
    else:
        raise ValueError("The user does not have access to this encryption key.")

@login_required
def request_support(request, transaction_pk):
    """
    Notifies the support team to join the chat.
    """
    transaction = get_object_or_404(Transaction, pk=transaction_pk)
    chat_key = get_object_or_404(ChatEncryptionKey, transaction=transaction)

    # Notify support via WebSocket
    notify_support(transaction, chat_key)

    return JsonResponse({'status': 'Support notified'})

@login_required
def leave_support(request, transaction_pk):
    """
    Notifies that the support team has left the chat.
    """
    transaction = get_object_or_404(Transaction, pk=transaction_pk)

    if request.user.is_staff:
        notify_support_left(transaction)
        return JsonResponse({'status': 'Support left the chat'})
    else:
        return JsonResponse({'status': 'Unauthorized'}, status=403)

def notify_support(transaction, chat_key):
    """
    Sends a notification to the support team via WebSocket.
    """
    notification_data = {
        'type': 'support.notification',
        'transaction_id': transaction.id,
        'buyer': transaction.buyer.username,
        'seller': transaction.seller.username,
        'encryption_key': {
            'buyer_key': chat_key.buyer_key,
            'seller_key': chat_key.seller_key
        }
    }

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'support_group',
        {
            'type': 'chat_message',
            'message': json.dumps(notification_data)
        }
    )

def notify_support_left(transaction):
    """
    Sends a notification to indicate the support team has left the chat.
    """
    notification_data = {
        'type': 'support_left',
        'transaction_id': transaction.id
    }

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'support_group',
        {
            'type': 'support_left',
            'message': json.dumps(notification_data)
        }
    )
