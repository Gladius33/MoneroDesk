from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Message, ChatEncryptionKey
from transactions.models import Transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from mimetypes import guess_type
from django.contrib import messages

# Formats autorisés
ALLOWED_FILE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/jpg', 'application/pdf']
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 Mo

@login_required
def chat_room_view(request, transaction_pk):
    transaction = get_object_or_404(Transaction, pk=transaction_pk)
    chat_key = get_object_or_404(ChatEncryptionKey, transaction=transaction)

    # Vérifiez si l'utilisateur fait partie de la transaction ou est membre du support
    if not (request.user == transaction.buyer or request.user == transaction.seller or request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You are not authorized to access this chat.")
        return redirect('some_other_view')  # Redirection vers une autre vue (ex: page d'accueil)

    if request.method == 'POST':
        text = request.POST.get('text')
        file = request.FILES.get('file')
        encrypted_text = encrypt_message(text, chat_key, request.user) if text else None
        encrypted_file = encrypt_file(file, chat_key, request.user) if file else None

        if text or file:
            Message.objects.create(
                transaction=transaction,
                sender=request.user,
                text=encrypted_text,
                file=encrypted_file
            )

    messages_list = decrypt_messages(transaction.messages.all(), chat_key, request.user)
    return render(request, 'chat/chat_room.html', {
        'transaction': transaction,
        'messages': messages_list
    })

def encrypt_message(message, chat_key, user):
    key = get_user_chat_key(chat_key, user)
    cipher = AES.new(base64.b64decode(key), AES.MODE_EAX)
    nonce = cipher.nonce
    ciphertext, tag = cipher.encrypt_and_digest(message.encode('utf-8'))
    return base64.b64encode(nonce + tag + ciphertext).decode('utf-8')

def decrypt_messages(messages, chat_key, user):
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
    key = get_user_chat_key(chat_key, user)
    data = base64.b64decode(encrypted_message)
    nonce, tag, ciphertext = data[:16], data[16:32], data[32:]
    cipher = AES.new(base64.b64decode(key), AES.MODE_EAX, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag).decode('utf-8')

def encrypt_file(file, chat_key, user):
    if file:
        validate_file(file)  # Validation de la taille et du type de fichier
        key = get_user_chat_key(chat_key, user)
        cipher = AES.new(base64.b64decode(key), AES.MODE_EAX)
        nonce = cipher.nonce
        file_data = file.read()
        ciphertext, tag = cipher.encrypt_and_digest(file_data)
        encrypted_file_data = base64.b64encode(nonce + tag + ciphertext)
        return encrypted_file_data

def validate_file(file: UploadedFile):
    """Validation du fichier uploadé en fonction de la taille et du type."""
    if file.size > MAX_FILE_SIZE:
        raise ValidationError("La taille du fichier dépasse la limite de 15 Mo.")
    
    # Vérification du type MIME (basé sur le contenu)
    file_type, _ = guess_type(file.name)
    if file_type not in ALLOWED_FILE_TYPES:
        raise ValidationError(f"Type de fichier invalide : {file_type}. Seules les images et les fichiers PDF sont autorisés.")
    
    # Vérification approfondie du type MIME par inspection du contenu du fichier
    if not is_valid_mime_type(file, file_type):
        raise ValidationError("Le contenu du fichier ne correspond pas à son extension. Upload rejeté.")

def is_valid_mime_type(file: UploadedFile, mime_type: str):
    """Vérification approfondie du type MIME en inspectant le contenu binaire du fichier."""
    try:
        if 'image' in mime_type:
            # Si c'est une image, essayer de la charger pour valider le contenu
            from PIL import Image
            img = Image.open(file)
            img.verify()  # Vérification que c'est bien un fichier image valide
        elif mime_type == 'application/pdf':
            # Vérification simple pour les fichiers PDF : s'assurer que le fichier commence par '%PDF'
            file.seek(0)  # Se déplacer au début du fichier
            return file.read(4) == b'%PDF'
        return True
    except Exception:
        return False

def get_user_chat_key(chat_key, user):
    if user == chat_key.transaction.buyer:
        return chat_key.buyer_key
    elif user == chat_key.transaction.seller:
        return chat_key.seller_key
    else:
        raise ValueError("L'utilisateur n'a pas accès à cette clé de chiffrement du chat.")

@login_required
def request_support(request, transaction_pk):
    transaction = get_object_or_404(Transaction, pk=transaction_pk)
    chat_key = get_object_or_404(ChatEncryptionKey, transaction=transaction)

    # Notifier le support via WebSocket
    notify_support(transaction, chat_key)

    return JsonResponse({'status': 'Support notified'})

@login_required
def leave_support(request, transaction_pk):
    transaction = get_object_or_404(Transaction, pk=transaction_pk)

    if request.user.is_staff or request.user.is_superuser:
        # Notifier que le support a quitté le chat
        notify_support_left(transaction)

        return JsonResponse({'status': 'Support left the chat'})
    else:
        return JsonResponse({'status': 'Unauthorized'}, status=403)

def notify_support(transaction, chat_key):
    # Préparation des données pour la notification
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

    # Envoi de la notification via WebSocket
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'support_group',  # Le groupe auquel tous les agents de support sont connectés
        {
            'type': 'chat_message',  # Le type de message
            'message': json.dumps(notification_data)
        }
    )

def notify_support_left(transaction):
    # Préparation des données pour notifier que le support a quitté
    notification_data = {
        'type': 'support_left',
        'transaction_id': transaction.id
    }

    # Envoi de la notification via WebSocket
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'support_group',
        {
            'type': 'support_left',
            'message': json.dumps(notification_data)
        }
    )
