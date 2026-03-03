"""Race control message fetching, parsing, and WebSocket broadcasting."""

import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils.dateparse import parse_datetime

from f1_pitwall.constants import FLAG_CHOICES
from f1_pitwall.exceptions import F1PitwallError
from f1_pitwall.models import RaceControlMessage, Session
from f1_pitwall.services.openf1_client import OpenF1Client

logger = logging.getLogger(__name__)

RACE_CONTROL_GROUP = 'race_control'
SC_CATEGORY = 'safetycar'
SC_END_MARKERS = ('ending', 'in this lap', 'withdrawn')
KNOWN_FLAGS = {value for value, _ in FLAG_CHOICES}


class RaceControlService:
    """Service for race control ingestion, queries, and websocket broadcasts."""

    def __init__(self, client=None, channel_layer=None):
        self.client = client or OpenF1Client()
        self.channel_layer = channel_layer or get_channel_layer()

    def get_messages(self, session_key):
        """Fetch race control messages, persist them, return session queryset."""
        session = self._session(session_key)
        if session is None:
            return RaceControlMessage.objects.none()

        raw_messages = self._fetch_messages(session_key)
        for raw in raw_messages:
            self._upsert_message(session, raw)

        return RaceControlMessage.objects.filter(session=session)

    def get_latest_flag(self, session_key):
        """Return latest non-empty flag for a session, else None."""
        self.get_messages(session_key)
        latest = RaceControlMessage.objects.filter(
            session__session_key=session_key,
        ).exclude(
            flag='',
        ).order_by('-timestamp').first()
        if latest is None:
            return None
        return latest.flag

    def is_safety_car_active(self, session_key):
        """Return True when latest safety car state indicates active."""
        self.get_messages(session_key)
        latest_sc = RaceControlMessage.objects.filter(
            session__session_key=session_key,
            category__iexact='SafetyCar',
        ).order_by('-timestamp').first()
        if latest_sc is None:
            return False
        message = (latest_sc.message or '').lower()
        return not any(marker in message for marker in SC_END_MARKERS)

    def broadcast_new_messages(self, session_key, since_timestamp):
        """Broadcast newly fetched messages (newer than since_timestamp)."""
        session = self._session(session_key)
        if session is None:
            return 0

        raw_messages = self._fetch_messages(session_key)
        broadcasted = 0

        for raw in raw_messages:
            obj, created = self._upsert_message(session, raw)
            if not created:
                continue
            if since_timestamp and obj.timestamp <= since_timestamp:
                continue
            self._broadcast(obj)
            broadcasted += 1
        return broadcasted

    def _fetch_messages(self, session_key):
        async def _fetch():
            return await self.client.get_race_control(session_key)

        try:
            return async_to_sync(_fetch)()
        except F1PitwallError as exc:
            logger.warning(
                'Race control fetch skipped for session %s: %s',
                session_key, exc,
            )
            return []

    def _upsert_message(self, session, raw):
        timestamp = parse_datetime(raw.get('date') or '')
        if timestamp is None:
            return None, False

        defaults = {
            'flag': self._normalize_flag(raw.get('flag')),
            'driver_number': raw.get('driver_number'),
            'lap_number': raw.get('lap_number'),
            'sector': raw.get('sector'),
        }
        return RaceControlMessage.objects.update_or_create(
            session=session,
            timestamp=timestamp,
            category=raw.get('category') or '',
            message=raw.get('message') or '',
            defaults=defaults,
        )

    def _normalize_flag(self, raw_flag):
        if not raw_flag:
            return ''
        normalized = str(raw_flag).upper().replace(' ', '_').replace('-', '_')
        if normalized in KNOWN_FLAGS:
            return normalized
        return ''

    def _broadcast(self, message):
        if not self.channel_layer:
            return
        payload = {
            'type': 'race_control',
            'id': str(message.id),
            'timestamp': message.timestamp.isoformat(),
            'category': message.category,
            'message': message.message,
            'flag': message.flag,
            'driver_number': message.driver_number,
            'lap_number': message.lap_number,
            'sector': message.sector,
        }
        async_to_sync(self.channel_layer.group_send)(
            RACE_CONTROL_GROUP,
            {'type': 'race_control_message', 'data': payload},
        )

    def _session(self, session_key):
        session = Session.objects.filter(session_key=session_key).first()
        if session is None:
            logger.warning(
                'Race control skipped: unknown session %s', session_key,
            )
        return session
