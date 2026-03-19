import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class TicketChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.ticket_id = self.scope['url_route']['kwargs']['ticket_id']
        self.room_group_name = f'ticket_{self.ticket_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'chat_message')

        if message_type == 'chat_message':
            # Broadcast the message to all clients in the room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': data.get('message', ''),
                    'sender_id': data.get('sender_id'),
                    'sender_name': data.get('sender_name'),
                    'sender_role': data.get('sender_role'),
                    'timestamp': data.get('timestamp', timezone.now().isoformat()),
                }
            )

    async def chat_message(self, event):
        """Send chat message to WebSocket client."""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender_id': event.get('sender_id'),
            'sender_name': event.get('sender_name'),
            'sender_role': event.get('sender_role'),
            'timestamp': event.get('timestamp'),
        }))

    async def ticket_updated(self, event):
        """Notify clients that the ticket was updated."""
        await self.send(text_data=json.dumps({
            'type': 'ticket_updated',
            'data': event.get('data', {}),
        }))
