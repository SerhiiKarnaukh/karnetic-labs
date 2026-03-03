"""End-to-end smoke test for F1 telemetry WebSocket."""

import asyncio
import json

import httpx
import websockets
from django.core.management.base import BaseCommand, CommandError

from accounts.models import Account


class Command(BaseCommand):
    help = 'Run E2E smoke test: JWT auth + telemetry websocket subscribe/replay'

    def add_arguments(self, parser):
        parser.add_argument('--base-url', default='http://127.0.0.1:8000')
        parser.add_argument('--ws-base-url', default='ws://127.0.0.1:8000')
        parser.add_argument('--session-key', type=int, default=9158)
        parser.add_argument('--driver-number', type=int, default=1)
        parser.add_argument('--email', default='ws_e2e@example.com')
        parser.add_argument('--password', default='ws_e2e_pass_123')

    def handle(self, *args, **options):
        user = self._ensure_active_user(
            options['email'],
            options['password'],
        )
        self.stdout.write(f'User ready: {user.email}')

        token = self._obtain_token(
            options['base_url'],
            options['email'],
            options['password'],
        )
        self.stdout.write('JWT obtained.')

        lap = self._resolve_lap(
            options['session_key'],
            options['driver_number'],
        )
        self.stdout.write(
            f"Using session={options['session_key']} driver={options['driver_number']} lap={lap}",
        )

        asyncio.run(
            self._run_ws_flow(
                options['ws_base_url'],
                options['session_key'],
                options['driver_number'],
                token,
                lap,
            ),
        )
        self.stdout.write(self.style.SUCCESS('E2E websocket smoke test: SUCCESS'))

    def _ensure_active_user(self, email, password):
        user, created = Account.objects.get_or_create(
            email=email,
            defaults={
                'first_name': 'WS',
                'last_name': 'E2E',
                'username': email.split('@')[0],
            },
        )
        user.set_password(password)
        user.is_active = True
        if created:
            user.save()
        else:
            user.save(update_fields=['password', 'is_active'])
        return user

    def _obtain_token(self, base_url, email, password):
        response = httpx.post(
            f'{base_url}/api/v1/token/',
            json={'email': email, 'password': password},
            timeout=20,
        )
        if response.status_code != 200:
            raise CommandError(
                f'Token endpoint failed: {response.status_code} {response.text}',
            )
        return response.json()['access']

    def _resolve_lap(self, session_key, driver_number):
        response = httpx.get(
            'https://api.openf1.org/v1/laps',
            params={'session_key': session_key, 'driver_number': driver_number},
            timeout=20,
        )
        if response.status_code != 200:
            return None
        rows = response.json()
        if not rows:
            return None
        return rows[0].get('lap_number')

    async def _run_ws_flow(
        self, ws_base_url, session_key, driver_number, token, lap,
    ):
        ws_url = (
            f'{ws_base_url}/ws/f1/telemetry/{session_key}/?token={token}'
        )
        async with websockets.connect(ws_url, open_timeout=10, close_timeout=5) as ws:
            await ws.send(json.dumps({
                'action': 'subscribe',
                'drivers': [driver_number],
            }))
            first = json.loads(await asyncio.wait_for(ws.recv(), timeout=25))
            if first.get('type') != 'telemetry':
                raise CommandError(f'Expected telemetry packet, got: {first}')
            self.stdout.write('Subscribe ok: telemetry packet received.')

            if lap is not None:
                await ws.send(json.dumps({'action': 'replay', 'lap': int(lap)}))
                replay = await self._wait_replay(ws)
                self.stdout.write(
                    f"Replay ok: driver={replay.get('driver')} lap={replay.get('lap')}",
                )
            else:
                self.stdout.write('Replay skipped: no lap found.')

            await ws.send(json.dumps({'action': 'unsubscribe'}))
            self.stdout.write('Unsubscribe sent.')

    async def _wait_replay(self, ws):
        for _ in range(12):
            payload = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
            if payload.get('type') == 'replay':
                return payload
        raise CommandError('Replay response not received.')
