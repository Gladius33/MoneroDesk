from django.test import TestCase
from django.urls import reverse
from models import ChatRoom
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

class TestChat(TestCase):

    def setUp(self):
        # Set up initial data, including AES key and chatroom
        self.key = get_random_bytes(32)  # AES-256 uses 32 bytes key
        self.chatroom = ChatRoom.objects.create(room_name='test_chat')

    def test_chatroom_creation(self):
        # Test chatroom creation
        self.assertEqual(self.chatroom.room_name, 'test_chat')

    def test_encrypt_chat_message(self):
        # Test AES-256 encryption of messages using PyCryptodome
        message = b'secret_message'
        cipher = AES.new(self.key, AES.MODE_CBC)  # CBC mode for encryption
        ciphertext = cipher.encrypt(pad(message, AES.block_size))  # Pad the message and encrypt
        self.assertIsNotNone(ciphertext)

        # Test decryption
        decipher = AES.new(self.key, AES.MODE_CBC, iv=cipher.iv)
        decrypted_message = unpad(decipher.decrypt(ciphertext), AES.block_size)
        self.assertEqual(decrypted_message, message)

    def test_support_join_leave_chat(self):
        # Test that support can join and leave the chatroom
        response = self.client.get(reverse('join_chat', args=[self.chatroom.id]))
        self.assertEqual(response.status_code, 200)
        self.client.get(reverse('leave_chat', args=[self.chatroom.id]))
        self.assertEqual(response.status_code, 200)

