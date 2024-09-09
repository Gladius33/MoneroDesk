import json
from channels.generic.websocket import AsyncWebsocketConsumer
from monero_app.services import MoneroService
from .models import Transaction

class TransactionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.transaction_id = self.scope['url_route']['kwargs']['transaction_id']
        self.room_group_name = f'transaction_{self.transaction_id}'

        # Join the WebSocket group for this transaction
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Fetch the initial confirmation status
        monero_service = MoneroService()
        escrow_address = self.get_escrow_address(self.transaction_id)
        confirmations = monero_service.get_confirmations(escrow_address)

        # Send initial confirmation status to the client
        await self.send(text_data=json.dumps({
            'type': 'confirmation_status',
            'confirmations': confirmations
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        if 'confirmations' in data:
            confirmations = data['confirmations']
            # Send updates to the group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'send_confirmation_update',
                    'confirmations': confirmations,
                }
            )

    async def send_confirmation_update(self, event):
        # Send confirmation update to WebSocket clients
        await self.send(text_data=json.dumps({
            'type': 'confirmation_status',
            'confirmations': event['confirmations']
        }))

    def get_escrow_address(self, transaction_id):
        # Function to fetch escrow address from transaction
        transaction = Transaction.objects.get(id=transaction_id)
        return transaction.escrow_wallet_address
