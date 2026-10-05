from asgiref.sync import async_to_sync
from django.test import TestCase, override_settings
from unittest.mock import AsyncMock

from social_notification.websocket.consumers import NotificationConsumer


@override_settings(
    CHANNEL_LAYERS={'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}}
)
class NotificationConsumerTests(TestCase):
    def setUp(self):
        self.consumer = NotificationConsumer()
        self.consumer.scope = {'url_route': {'kwargs': {'user_id': '42'}}}
        self.consumer.channel_name = 'channel'
        self.consumer.channel_layer = AsyncMock()
        self.consumer.accept = AsyncMock()
        self.consumer.send = AsyncMock()

    def test_connects_adds_consumer_to_notification_group(self):
        async_to_sync(self.consumer.connect)()

        self.consumer.channel_layer.group_add.assert_awaited_once_with(
            'notifications_42', 'channel'
        )
        self.consumer.accept.assert_awaited_once()

    def test_disconnects_and_sends_notification(self):
        self.consumer.group_name = 'notifications_42'

        async_to_sync(self.consumer.disconnect)(1000)
        async_to_sync(self.consumer.send_notification)({'message': 'New notification'})

        self.consumer.channel_layer.group_discard.assert_awaited_once_with(
            'notifications_42', 'channel'
        )
        self.consumer.send.assert_awaited_once_with(
            text_data='{"message": "New notification"}'
        )
