"""Orchestrates telemetry flow from OpenF1 to DB and websocket channels."""

import logging
import time

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.utils.dateparse import parse_datetime

from f1_pitwall.models import Driver, Session, TelemetrySnapshot
from f1_pitwall.services.openf1_client import OpenF1Client

logger = logging.getLogger(__name__)

TELEMETRY_GROUP_PREFIX = 'telemetry_'
STATUS_NOT_STARTED = 'not_started'
STATUS_LIVE = 'live'
STATUS_COMPLETE = 'complete'


class TelemetryEngine:
    """Fetches telemetry, broadcasts updates, and persists snapshots."""

    def __init__(
        self,
        client=None,
        channel_layer=None,
        persist_snapshots=True,
        use_celery_persistence=False,
        poll_interval_seconds=1.0,
    ):
        self.client = client or OpenF1Client()
        self.channel_layer = channel_layer or get_channel_layer()
        self.persist_snapshots = persist_snapshots
        self.use_celery_persistence = use_celery_persistence
        self.poll_interval_seconds = poll_interval_seconds
        self._sessions = {}

    def start_live_session(self, session_key):
        """Begin tracking a live session for polling."""
        state = self._sessions.get(session_key, {})
        state['status'] = STATUS_LIVE
        state.setdefault('last_timestamp', None)
        self._sessions[session_key] = state

    def stop_live_session(self, session_key):
        """Stop tracking a session."""
        state = self._sessions.get(session_key, {})
        state['status'] = STATUS_COMPLETE
        self._sessions[session_key] = state

    def get_session_status(self, session_key):
        """Return not_started/live/complete for a session key."""
        if session_key not in self._sessions:
            return STATUS_NOT_STARTED
        return self._sessions[session_key].get('status', STATUS_NOT_STARTED)

    def poll_telemetry(self, session_key, driver_numbers, since_timestamp=None):
        """Fetch new telemetry rows for drivers, broadcast, optionally persist."""
        snapshots = self._fetch_snapshots(
            session_key, driver_numbers, since_timestamp,
        )
        if not snapshots:
            return []

        self._broadcast_snapshots(session_key, snapshots)
        if self.persist_snapshots:
            self._persist_snapshots(session_key, snapshots)
        self._update_last_timestamp(session_key, snapshots)
        return snapshots

    def snapshot_all_drivers(self, session_key):
        """Fetch and persist one polling cycle for all active drivers."""
        drivers = self._active_driver_numbers()
        since = self._last_timestamp(session_key)
        return self.poll_telemetry(session_key, drivers, since)

    def run_polling_loop(
        self,
        session_key,
        driver_numbers=None,
        max_iterations=None,
    ):
        """Run polling loop while session is live (testable with max_iterations)."""
        self.start_live_session(session_key)
        drivers = driver_numbers or self._active_driver_numbers()
        iterations = 0

        while self.get_session_status(session_key) == STATUS_LIVE:
            since = self._last_timestamp(session_key)
            self.poll_telemetry(session_key, drivers, since)
            iterations += 1
            if max_iterations and iterations >= max_iterations:
                break
            time.sleep(self.poll_interval_seconds)

    def _fetch_snapshots(self, session_key, driver_numbers, since_timestamp):
        snapshots = []
        for driver_number in driver_numbers:
            rows = self._fetch_driver_rows(
                session_key, driver_number, since_timestamp,
            )
            for row in rows:
                normalized = self._normalize_row(driver_number, row)
                if normalized:
                    snapshots.append(normalized)
        return snapshots

    def _fetch_driver_rows(self, session_key, driver_number, since_timestamp):
        async def _fetch():
            return await self.client.get_car_data(
                session_key=session_key,
                driver_number=driver_number,
                date_gt=since_timestamp,
            )

        return async_to_sync(_fetch)()

    def _normalize_row(self, driver_number, row):
        timestamp = parse_datetime(row.get('date') or '')
        if timestamp is None:
            return None
        return {
            'driver_number': driver_number,
            'timestamp': timestamp,
            'speed': int(row.get('speed') or 0),
            'rpm': int(row.get('rpm') or 0),
            'throttle': int(row.get('throttle') or 0),
            'brake': int(row.get('brake') or 0),
            'gear': int(row.get('n_gear') or 0),
            'drs': int(row.get('drs') or 0),
            'raw': row,
        }

    def _broadcast_snapshots(self, session_key, snapshots):
        if not self.channel_layer:
            return
        group = f'{TELEMETRY_GROUP_PREFIX}{session_key}'
        for snapshot in snapshots:
            payload = {
                'type': 'telemetry',
                'driver': snapshot['driver_number'],
                'data': snapshot['raw'],
            }
            async_to_sync(self.channel_layer.group_send)(
                group,
                {'type': 'telemetry_message', 'data': payload},
            )

    def _persist_snapshots(self, session_key, snapshots):
        if self.use_celery_persistence:
            self._enqueue_snapshot_task(session_key, snapshots)
            return
        self._persist_snapshots_sync(session_key, snapshots)

    def _drivers_by_number(self, snapshots):
        numbers = {snap['driver_number'] for snap in snapshots}
        queryset = Driver.objects.filter(driver_number__in=numbers)
        return {d.driver_number: d for d in queryset}

    def _build_snapshot_objects(self, session, drivers, snapshots):
        objects = []
        for snap in snapshots:
            driver = drivers.get(snap['driver_number'])
            if driver is None:
                continue
            objects.append(TelemetrySnapshot(
                session=session,
                driver=driver,
                timestamp=snap['timestamp'],
                speed=snap['speed'],
                rpm=snap['rpm'],
                throttle=snap['throttle'],
                brake=snap['brake'],
                gear=snap['gear'],
                drs=snap['drs'],
            ))
        return objects

    def _active_driver_numbers(self):
        return list(Driver.objects.filter(
            is_active=True,
        ).values_list('driver_number', flat=True))

    def _last_timestamp(self, session_key):
        return self._sessions.get(session_key, {}).get('last_timestamp')

    def _update_last_timestamp(self, session_key, snapshots):
        if not snapshots:
            return
        latest = max(snap['timestamp'] for snap in snapshots).isoformat()
        state = self._sessions.get(session_key, {})
        state['last_timestamp'] = latest
        self._sessions[session_key] = state

    def _enqueue_snapshot_task(self, session_key, snapshots):
        """Send persistence job to Celery; fallback to sync on enqueue failure."""
        from f1_pitwall.tasks.collect_telemetry import collect_telemetry_snapshot

        payload = self._serialize_task_payload(snapshots)
        try:
            collect_telemetry_snapshot.delay(session_key, payload)
        except Exception as exc:
            logger.warning('Telemetry enqueue failed, persisting inline: %s', exc)
            self._persist_snapshots_sync(session_key, snapshots)

    def _serialize_task_payload(self, snapshots):
        payload = []
        for snap in snapshots:
            payload.append({
                'driver_number': snap['driver_number'],
                'timestamp': snap['timestamp'].isoformat(),
                'speed': snap['speed'],
                'rpm': snap['rpm'],
                'throttle': snap['throttle'],
                'brake': snap['brake'],
                'gear': snap['gear'],
                'drs': snap['drs'],
            })
        return payload

    def _persist_snapshots_sync(self, session_key, snapshots):
        session = Session.objects.filter(session_key=session_key).first()
        if session is None:
            logger.warning(
                'Telemetry persistence skipped: unknown session %s', session_key,
            )
            return
        drivers = self._drivers_by_number(snapshots)
        to_create = self._build_snapshot_objects(session, drivers, snapshots)
        if not to_create:
            return
        with transaction.atomic():
            TelemetrySnapshot.objects.bulk_create(to_create, batch_size=1000)
