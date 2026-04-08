"""On-demand hydration for lap and telemetry endpoints."""

import logging
from datetime import timedelta

from asgiref.sync import async_to_sync
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from f1_pitwall.exceptions import F1PitwallError
from f1_pitwall.models import Driver, LapData, TelemetrySnapshot
from f1_pitwall.services.openf1_client import OpenF1Client

logger = logging.getLogger(__name__)


class SessionDataHydrator:
    """Hydrate missing DB rows from OpenF1 on endpoint reads."""

    def __init__(self, client=None):
        self.client = client or OpenF1Client()

    def ensure_laps(self, session, driver_number=None):
        """Load lap rows for a session when local table is empty."""
        if not self._enabled() or self._has_laps(session, driver_number):
            return
        rows = self._fetch_laps(session.session_key, driver_number)
        self._upsert_laps(session, rows)

    def ensure_latest_snapshots(self, session, driver_number=None):
        """Load latest telemetry rows per driver when table is empty."""
        if not self._enabled() or self._has_telemetry(session, driver_number):
            return
        drivers = self._driver_numbers(driver_number)
        snapshots = self._fetch_latest_snapshots(session, drivers)
        if not snapshots:
            snapshots = self._fallback_snapshots_from_laps(session, drivers)
        self._create_snapshots(session, snapshots)

    def _enabled(self):
        return bool(getattr(settings, 'F1_AUTO_HYDRATE_READ', False))

    def _has_laps(self, session, driver_number):
        queryset = LapData.objects.filter(session=session)
        if driver_number:
            queryset = queryset.filter(driver__driver_number=driver_number)
        return queryset.exists()

    def _has_telemetry(self, session, driver_number):
        queryset = TelemetrySnapshot.objects.filter(session=session)
        if driver_number:
            queryset = queryset.filter(driver__driver_number=driver_number)
        return queryset.exists()

    def _fetch_laps(self, session_key, driver_number):
        async def _fetch():
            return await self.client.get_lap_data(session_key, driver_number)

        try:
            return async_to_sync(_fetch)()
        except F1PitwallError as exc:
            logger.warning('Lap hydrate skipped for session %s: %s', session_key, exc)
            return []

    def _upsert_laps(self, session, rows):
        for row in rows:
            driver = self._driver(row.get('driver_number'))
            lap_number = self._to_int(row.get('lap_number'))
            if driver is None or lap_number is None:
                continue
            LapData.objects.update_or_create(
                session=session,
                driver=driver,
                lap_number=lap_number,
                defaults=self._lap_defaults(row),
            )

    def _lap_defaults(self, row):
        return {
            'lap_duration': self._to_float(row.get('lap_duration')),
            'sector_1': self._to_float(row.get('duration_sector_1')),
            'sector_2': self._to_float(row.get('duration_sector_2')),
            'sector_3': self._to_float(row.get('duration_sector_3')),
            'speed_trap': self._to_float(
                row.get('st_speed', row.get('speed_trap')),
            ),
            'is_pit_out_lap': self._to_bool(row.get('is_pit_out_lap')),
            'is_pit_in_lap': self._to_bool(row.get('is_pit_in_lap')),
            'is_personal_best': self._to_bool(row.get('is_personal_best')),
        }

    def _driver_numbers(self, explicit_driver):
        if explicit_driver:
            number = self._to_int(explicit_driver)
            return [number] if number is not None else []
        return list(
            Driver.objects.filter(is_active=True).values_list(
                'driver_number', flat=True,
            ),
        )

    def _fetch_latest_snapshots(self, session, driver_numbers):
        if not driver_numbers:
            return []

        async def _fetch_batch(date_gt):
            rows = {}
            for driver_number in driver_numbers:
                rows[driver_number] = await self._safe_fetch_car_data(
                    session.session_key, driver_number, date_gt,
                )
            return rows

        date_gt = self._date_gt_hint(session)
        try:
            batches = async_to_sync(_fetch_batch)(date_gt)
            if date_gt and not any(batches.values()):
                batches = async_to_sync(_fetch_batch)(None)
            return self._extract_latest_snapshots(batches)
        except F1PitwallError as exc:
            logger.warning(
                'Telemetry hydrate skipped for session %s: %s',
                session.session_key,
                exc,
            )
            return []
        except RuntimeError as exc:
            logger.warning(
                'Telemetry hydrate runtime issue for session %s: %s',
                session.session_key,
                exc,
            )
            return []

    def _extract_latest_snapshots(self, batches):
        snapshots = []
        for driver_number, rows in batches.items():
            latest = self._latest_row(rows)
            if latest is None:
                continue
            snapshots.append({'driver_number': driver_number, 'row': latest})
        return snapshots

    async def _safe_fetch_car_data(self, session_key, driver_number, date_gt):
        try:
            return await self.client.get_car_data(
                session_key=session_key,
                driver_number=driver_number,
                date_gt=date_gt,
            )
        except F1PitwallError as exc:
            logger.warning(
                'Telemetry hydrate skipped for session %s driver %s: %s',
                session_key,
                driver_number,
                exc,
            )
            return []

    def _date_gt_hint(self, session):
        if session.date_end is None:
            return None
        return (session.date_end - timedelta(minutes=5)).isoformat()

    def _latest_row(self, rows):
        if not rows:
            return None
        dated = [row for row in rows if parse_datetime(row.get('date') or '')]
        if not dated:
            return None
        return max(dated, key=lambda row: parse_datetime(row.get('date')))

    def _create_snapshots(self, session, snapshots):
        objects = []
        for item in snapshots:
            driver = self._driver(item['driver_number'])
            normalized = self._normalize_snapshot(item['row'])
            if driver is None or normalized is None:
                continue
            objects.append(TelemetrySnapshot(
                session=session,
                driver=driver,
                **normalized,
            ))
        if objects:
            TelemetrySnapshot.objects.bulk_create(objects, batch_size=200)

    def _fallback_snapshots_from_laps(self, session, driver_numbers):
        query = LapData.objects.filter(session=session).order_by(
            'driver__driver_number', '-lap_number',
        )
        if driver_numbers:
            query = query.filter(driver__driver_number__in=driver_numbers)

        seen = set()
        rows = []
        fallback_timestamp = timezone.now().isoformat()
        for lap in query:
            number = lap.driver.driver_number
            if number in seen:
                continue
            seen.add(number)
            rows.append({
                'driver_number': number,
                'row': {
                    'date': fallback_timestamp,
                    'speed': int(round(lap.speed_trap or 0)),
                    'rpm': 0,
                    'throttle': 0,
                    'brake': 0,
                    'n_gear': 0,
                    'drs': 0,
                    'data_source': 'fallback_lap_speed_trap',
                    'is_fallback': True,
                },
            })
        return rows

    def _normalize_snapshot(self, row):
        timestamp = parse_datetime(row.get('date') or '')
        if timestamp is None:
            return None
        return {
            'timestamp': timestamp,
            'speed': self._to_int(row.get('speed')) or 0,
            'rpm': self._to_int(row.get('rpm')) or 0,
            'throttle': self._to_int(row.get('throttle')) or 0,
            'brake': self._to_int(row.get('brake')) or 0,
            'gear': self._to_int(row.get('n_gear')) or 0,
            'drs': self._to_int(row.get('drs')) or 0,
            'data_source': row.get('data_source') or 'openf1_car_data',
            'is_fallback': bool(row.get('is_fallback')),
        }

    def _driver(self, driver_number):
        if driver_number is None:
            return None
        return Driver.objects.filter(driver_number=driver_number).first()

    def _to_int(self, value):
        if value in (None, ''):
            return None
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    def _to_float(self, value):
        if value in (None, ''):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _to_bool(self, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value > 0
        if isinstance(value, str):
            return value.strip().lower() in {'1', 'true', 'yes', 'y'}
        return False
