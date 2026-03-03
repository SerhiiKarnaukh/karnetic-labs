"""AsyncWebsocketConsumer for real-time telemetry data streaming."""

import asyncio
import json
import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model

from ..services.openf1_client import OpenF1Client

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 1
RETRY_INTERVAL_SECONDS = 5
WS_CONNECT_CODE = 101
WS_DISCONNECT_CODE = 1000
WS_METHOD = 'WS'
UNKNOWN_IP = '127.0.0.1'
UNKNOWN_AGENT = ''


class TelemetryConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for telemetry subscribe/unsubscribe/replay."""

    async def connect(self):
        self.session_key = int(self.scope['url_route']['kwargs']['session_key'])
        self.group_name = f'telemetry_{self.session_key}'
        self.client = OpenF1Client()
        self.selected_drivers = []
        self.streaming = False
        self.streaming_task = None
        self.last_timestamps = {}
        self.user = await self._resolve_user()
        if self.user is None:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self._log_ws_event(WS_CONNECT_CODE)

    async def disconnect(self, close_code):
        await self._stop_streaming()
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        await self.client.close()
        await self._log_ws_event(WS_DISCONNECT_CODE)

    async def receive(self, text_data=None, bytes_data=None):
        payload = self._parse_payload(text_data)
        if payload is None:
            await self._send_error('Invalid JSON payload.')
            return

        action = payload.get('action')
        if action == 'subscribe':
            await self._handle_subscribe(payload)
            return
        if action == 'unsubscribe':
            await self._handle_unsubscribe()
            return
        if action == 'replay':
            await self._handle_replay(payload)
            return
        await self._send_error(f'Unknown action: {action}')

    async def telemetry_message(self, event):
        await self.send(text_data=json.dumps(event['data']))

    def _parse_payload(self, text_data):
        try:
            return json.loads(text_data or '{}')
        except json.JSONDecodeError:
            return None

    async def _handle_subscribe(self, payload):
        drivers = payload.get('drivers') or []
        if not isinstance(drivers, list) or not drivers:
            await self._send_error('Subscribe requires non-empty "drivers" list.')
            return

        self.selected_drivers = [int(driver) for driver in drivers]
        self.last_timestamps = {}
        if self.streaming:
            return

        self.streaming = True
        self.streaming_task = asyncio.create_task(self._poll_loop())

    async def _handle_unsubscribe(self):
        await self._stop_streaming()
        self.selected_drivers = []
        self.last_timestamps = {}

    async def _handle_replay(self, payload):
        lap = payload.get('lap')
        if not isinstance(lap, int):
            await self._send_error('Replay requires integer "lap".')
            return
        if not self.selected_drivers:
            await self._send_error('Replay requires subscribed drivers.')
            return

        for driver in self.selected_drivers:
            lap_rows = await self.client.get_lap_data(
                session_key=self.session_key, driver_number=driver,
            )
            for row in lap_rows:
                if row.get('lap_number') != lap:
                    continue
                await self.send(text_data=json.dumps({
                    'type': 'replay',
                    'driver': driver,
                    'lap': lap,
                    'data': row,
                }))

    async def _poll_loop(self):
        while self.streaming:
            try:
                await self._stream_once()
                await asyncio.sleep(POLL_INTERVAL_SECONDS)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning('Telemetry poll error: %s', exc)
                await self._send_error(str(exc))
                await asyncio.sleep(RETRY_INTERVAL_SECONDS)

    async def _stream_once(self):
        for driver in self.selected_drivers:
            row = await self._latest_driver_row(driver)
            if row is None:
                continue
            await self.send(text_data=json.dumps({
                'type': 'telemetry',
                'driver': driver,
                'data': row,
            }))

    async def _latest_driver_row(self, driver):
        rows = await self.client.get_car_data(
            session_key=self.session_key,
            driver_number=driver,
            date_gt=self.last_timestamps.get(driver),
        )
        if not rows:
            return None
        latest = rows[-1]
        self.last_timestamps[driver] = latest.get('date')
        return latest

    async def _stop_streaming(self):
        self.streaming = False
        if self.streaming_task is None:
            return
        self.streaming_task.cancel()
        try:
            await self.streaming_task
        except asyncio.CancelledError:
            pass
        self.streaming_task = None

    async def _send_error(self, message):
        await self.send(text_data=json.dumps({'type': 'error', 'message': message}))

    async def _resolve_user(self):
        from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
        from rest_framework_simplejwt.tokens import AccessToken

        token = self._query_param('token')
        if not token:
            return None
        try:
            access = AccessToken(token)
        except (InvalidToken, TokenError):
            return None
        user_id = access.get('user_id')
        if user_id is None:
            return None
        return await self._get_user(user_id)

    def _query_param(self, key):
        query = parse_qs((self.scope.get('query_string') or b'').decode())
        values = query.get(key)
        if not values:
            return None
        return values[0]

    @database_sync_to_async
    def _get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def _log_ws_event(self, status_code):
        from ..models import APIAuditLog

        APIAuditLog.objects.create(
            user=self.user,
            method=WS_METHOD,
            path=self.scope.get('path', ''),
            ip_address=self._client_ip(),
            user_agent=self._user_agent(),
            status_code=status_code,
            response_time_ms=0.0,
        )

    def _client_ip(self):
        client = self.scope.get('client')
        if not client:
            return UNKNOWN_IP
        return client[0] or UNKNOWN_IP

    def _user_agent(self):
        headers = dict(self.scope.get('headers') or [])
        return headers.get(b'user-agent', b'').decode() or UNKNOWN_AGENT
