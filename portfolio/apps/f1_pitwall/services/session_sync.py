"""Session and driver metadata synchronization from OpenF1 API."""

import logging

from asgiref.sync import async_to_sync
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from f1_pitwall.models import Driver, Session
from f1_pitwall.services.openf1_client import OpenF1Client

logger = logging.getLogger(__name__)

SESSION_TYPE_MAP = {
    'practice': 'practice',
    'qualifying': 'qualifying',
    'sprint': 'sprint',
    'sprint qualifying': 'qualifying',
    'sprint shootout': 'qualifying',
    'race': 'race',
}

# Driver numbers that are not real racing entries
NON_RACING_DRIVER_PREFIXES = ('FOM', 'FIA')
NON_RACING_NAME_KEYWORDS = ('TEST CAR', 'SAFETY CAR', 'MEDICAL CAR')


class SessionSyncService:
    """Synchronizes session and driver data from OpenF1 into local DB."""

    def sync_sessions(self, year=None):
        """Pull sessions from OpenF1 and create/update local records."""
        raw_sessions = self._fetch_sessions(year)
        created, updated = 0, 0

        for raw in raw_sessions:
            was_created = self._upsert_session(raw)
            if was_created:
                created += 1
            else:
                updated += 1

        logger.info(
            "Session sync complete: %d created, %d updated",
            created, updated,
        )
        return {'created': created, 'updated': updated}

    def sync_drivers(self, session_key=None):
        """Pull driver info from OpenF1 and create/update local records."""
        raw_drivers = self._fetch_drivers(session_key)
        created, updated = 0, 0

        for raw in raw_drivers:
            was_created = self._upsert_driver(raw)
            if was_created:
                created += 1
            else:
                updated += 1

        logger.info(
            "Driver sync complete: %d created, %d updated",
            created, updated,
        )
        return {'created': created, 'updated': updated}

    def get_available_sessions(self, year, session_type=None):
        """Return filtered session queryset for the frontend."""
        qs = Session.objects.filter(year=year)
        if session_type:
            qs = qs.filter(session_type=session_type)
        return qs

    def detect_live_session(self):
        """Return the currently live session, or None."""
        now = timezone.now()
        return Session.objects.filter(
            date_start__lte=now,
            date_end__gte=now,
            is_live=True,
        ).first()

    # -- Internal helpers ----------------------------------------------------

    def _fetch_sessions(self, year):
        """Call OpenF1 API for sessions (async bridged to sync)."""
        async def _fetch():
            client = OpenF1Client()
            try:
                return await client.get_sessions(year=year)
            finally:
                await client.close()

        return async_to_sync(_fetch)()

    def _fetch_drivers(self, session_key):
        """Call OpenF1 API for drivers (async bridged to sync)."""
        async def _fetch():
            client = OpenF1Client()
            try:
                return await client.get_drivers(session_key=session_key)
            finally:
                await client.close()

        return async_to_sync(_fetch)()

    def _upsert_session(self, raw):
        """Create or update a single Session from API data. Returns True if created."""
        session_key = raw.get('session_key')
        if not session_key:
            return False

        defaults = {
            'meeting_key': raw.get('meeting_key') or 0,
            'session_name': raw.get('session_name') or '',
            'session_type': self._resolve_session_type(
                raw.get('session_type') or '',
                raw.get('session_name') or '',
            ),
            'circuit_name': raw.get('location') or '',
            'circuit_short_name': (raw.get('circuit_short_name') or '')[:20],
            'country_name': raw.get('country_name') or '',
            'country_code': (raw.get('country_code') or '')[:3],
            'date_start': parse_datetime(raw['date_start']),
            'date_end': self._parse_optional_datetime(raw.get('date_end')),
            'year': raw.get('year') or 0,
        }

        _, created = Session.objects.update_or_create(
            session_key=session_key,
            defaults=defaults,
        )
        return created

    def _upsert_driver(self, raw):
        """Create or update a single Driver from API data. Returns True if created."""
        driver_number = raw.get('driver_number')
        if not driver_number:
            return False

        colour = raw.get('team_colour') or ''
        if colour and not colour.startswith('#'):
            colour = f'#{colour}'

        defaults = self._build_driver_defaults(raw, colour)

        _, created = Driver.objects.update_or_create(
            driver_number=driver_number,
            defaults=defaults,
        )
        return created

    def _build_driver_defaults(self, raw, colour):
        """Build defaults dict, skipping empty values for existing records."""
        full_name = raw.get('full_name') or ''
        candidate = {
            'full_name': full_name,
            'name_acronym': (raw.get('name_acronym') or '')[:3],
            'team_name': raw.get('team_name') or '',
            'team_colour': colour[:7],
            'headshot_url': raw.get('headshot_url') or '',
            'country_code': (raw.get('country_code') or '')[:3],
            'is_active': not self._is_non_racing_entry(full_name),
        }
        # Only include non-empty values so we don't overwrite good data
        # Always include is_active — it must be set explicitly
        return {
            k: v for k, v in candidate.items()
            if v or k == 'is_active'
        }

    def _is_non_racing_entry(self, full_name):
        """Check if the driver entry is a non-racing vehicle (FOM/FIA)."""
        upper = full_name.upper()
        return any(kw in upper for kw in NON_RACING_NAME_KEYWORDS)

    def _resolve_session_type(self, api_type, session_name):
        """Determine session_type from both API type and session name.

        OpenF1 returns session_type='Race' for Sprint races, so we use
        session_name to distinguish sprints from main races.
        """
        name_lower = session_name.lower()
        if name_lower == 'sprint':
            return 'sprint'
        if 'sprint' in name_lower and 'qualifying' in name_lower:
            return 'qualifying'
        if 'sprint' in name_lower and 'shootout' in name_lower:
            return 'qualifying'
        return SESSION_TYPE_MAP.get(api_type.lower(), 'practice')

    def _parse_optional_datetime(self, value):
        """Parse a datetime string or return None."""
        if not value:
            return None
        return parse_datetime(value)
