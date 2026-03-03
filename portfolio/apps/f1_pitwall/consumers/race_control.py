"""AsyncWebsocketConsumer for broadcasting race control messages."""

import json

from channels.generic.websocket import AsyncWebsocketConsumer


class RaceControlConsumer(AsyncWebsocketConsumer):
    """Broadcast-only race control stream."""

    group_name = 'race_control'

    async def connect(self):
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': 'Race control stream is broadcast-only.',
        }))

    async def race_control_message(self, event):
        await self.send(text_data=json.dumps(event['data']))
