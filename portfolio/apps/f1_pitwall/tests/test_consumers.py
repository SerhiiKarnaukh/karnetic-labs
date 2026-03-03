"""Tests for F1 WebSocket consumers."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

from asgiref.sync import async_to_sync
from channels.layers import InMemoryChannelLayer
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from rest_framework_simplejwt.tokens import AccessToken

from f1_pitwall.consumers.race_control import RaceControlConsumer
from f1_pitwall.consumers.telemetry import TelemetryConsumer

User = get_user_model()


class TelemetryConsumerTest(TransactionTestCase):
    """Lifecycle and command handling tests for TelemetryConsumer."""

    def setUp(self):
        self.user = User.objects.create_user(
            first_name='WS',
            last_name='Tester',
            username='ws_tester',
            email='ws_tester@example.com',
            password='pass12345',
        )
        self.user.is_active = True
        self.user.save(update_fields=['is_active'])
        self.token = str(AccessToken.for_user(self.user))

    def _build_scope(self, token=None):
        token_value = token or self.token
        query = f'token={token_value}'.encode()
        return {
            'type': 'websocket',
            'path': '/ws/f1/telemetry/9158/',
            'query_string': query,
            'url_route': {'kwargs': {'session_key': '9158'}},
            'client': ('127.0.0.1', 5000),
            'headers': [],
        }

    def _build_consumer(self, token=None):
        consumer = TelemetryConsumer()
        consumer.scope = self._build_scope(token=token)
        consumer.channel_name = 'test-channel'
        consumer.channel_layer = InMemoryChannelLayer()
        consumer.accept = AsyncMock()
        consumer.close = AsyncMock()
        consumer.send = AsyncMock()
        return consumer

    def test_rejects_invalid_jwt_token(self):
        async def _run():
            consumer = self._build_consumer(token='invalid.jwt.token')
            await consumer.connect()
            consumer.close.assert_awaited_once()
            consumer.accept.assert_not_called()

        async_to_sync(_run)()

    @patch('f1_pitwall.consumers.telemetry.POLL_INTERVAL_SECONDS', 0.01)
    @patch('f1_pitwall.consumers.telemetry.OpenF1Client')
    def test_subscribe_unsubscribe_lifecycle(self, mock_client_cls):
        client = MagicMock()
        client.get_car_data = AsyncMock(side_effect=[
            [{'date': '2026-03-01T12:00:00Z', 'speed': 320}],
            [],
            [],
        ])
        client.close = AsyncMock()
        mock_client_cls.return_value = client

        async def _run():
            consumer = self._build_consumer()
            await consumer.connect()
            consumer.accept.assert_awaited_once()

            await consumer.receive(text_data=json.dumps({
                'action': 'subscribe',
                'drivers': [44],
            }))
            await asyncio.sleep(0.02)

            sent_payloads = [
                json.loads(kwargs['text_data'])
                for _, kwargs in consumer.send.await_args_list
            ]
            telemetry = [msg for msg in sent_payloads if msg.get('type') == 'telemetry']
            self.assertTrue(telemetry)
            self.assertEqual(telemetry[0]['driver'], 44)
            self.assertEqual(telemetry[0]['data']['speed'], 320)

            await consumer.receive(text_data=json.dumps({'action': 'unsubscribe'}))
            self.assertFalse(consumer.streaming)

            await consumer.disconnect(1000)
            client.close.assert_awaited_once()

        async_to_sync(_run)()

    @patch('f1_pitwall.consumers.telemetry.OpenF1Client')
    def test_replay_returns_exact_requested_lap(self, mock_client_cls):
        client = MagicMock()
        client.get_car_data = AsyncMock(return_value=[])
        client.get_lap_data = AsyncMock(return_value=[
            {'lap_number': 14, 'lap_duration': 91.5},
            {'lap_number': 15, 'lap_duration': 90.2},
        ])
        client.close = AsyncMock()
        mock_client_cls.return_value = client

        async def _run():
            consumer = self._build_consumer()
            await consumer.connect()
            await consumer.receive(text_data=json.dumps({
                'action': 'subscribe',
                'drivers': [1],
            }))
            await consumer.receive(text_data=json.dumps({
                'action': 'replay',
                'lap': 15,
            }))

            sent_payloads = [
                json.loads(kwargs['text_data'])
                for _, kwargs in consumer.send.await_args_list
            ]
            replay = [msg for msg in sent_payloads if msg.get('type') == 'replay']
            self.assertEqual(len(replay), 1)
            self.assertEqual(replay[0]['driver'], 1)
            self.assertEqual(replay[0]['lap'], 15)
            self.assertEqual(replay[0]['data']['lap_number'], 15)

            await consumer.disconnect(1000)

        async_to_sync(_run)()


class RaceControlConsumerTest(TransactionTestCase):
    """Broadcast handler tests for RaceControlConsumer."""

    def test_race_control_message_sends_json(self):
        async def _run():
            consumer = RaceControlConsumer()
            consumer.scope = {
                'type': 'websocket',
                'path': '/ws/f1/race-control/',
            }
            consumer.channel_name = 'test-channel'
            consumer.channel_layer = InMemoryChannelLayer()
            consumer.send = AsyncMock()
            consumer.accept = AsyncMock()

            await consumer.connect()
            await consumer.race_control_message({
                'data': {'type': 'race_control', 'message': 'SC DEPLOYED'},
            })
            consumer.send.assert_awaited_once_with(
                text_data='{"type": "race_control", "message": "SC DEPLOYED"}',
            )

            await consumer.disconnect(1000)

        async_to_sync(_run)()
