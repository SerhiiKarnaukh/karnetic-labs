from asgiref.sync import async_to_sync
from django.test import TestCase, override_settings
from unittest.mock import AsyncMock

from social_chat.websocket.consumers import SocialChatConsumer


@override_settings(
    CHANNEL_LAYERS={'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}}
)
class SocialChatConsumerTests(TestCase):
    def setUp(self):
        self.consumer = SocialChatConsumer()
        self.consumer.scope = {
            'url_route': {'kwargs': {'conversation_id': 'abc-123', 'user_id': '42'}}
        }
        self.consumer.channel_name = 'channel'
        self.consumer.channel_layer = AsyncMock()
        self.consumer.accept = AsyncMock()
        self.consumer.close = AsyncMock()
        self.consumer.send = AsyncMock()

    def test_connects_adds_consumer_to_conversation_group(self):
        async_to_sync(self.consumer.connect)()

        self.consumer.channel_layer.group_add.assert_awaited_once_with(
            'social_chat_abc-123', 'channel'
        )
        self.consumer.accept.assert_awaited_once()

    def test_disconnects_and_sends_group_message(self):
        self.consumer.group_name = 'social_chat_abc-123'

        async_to_sync(self.consumer.disconnect)(1000)
        async_to_sync(self.consumer.send_message)({'message': 'Hello'})

        self.consumer.channel_layer.group_discard.assert_awaited_once_with(
            'social_chat_abc-123', 'channel'
        )
        self.consumer.send.assert_awaited_once_with(text_data='{"message": "Hello"}')

    def test_rejects_connection_without_user_id(self):
        self.consumer.scope['url_route']['kwargs']['user_id'] = None

        async_to_sync(self.consumer.connect)()

        self.consumer.close.assert_awaited_once()
