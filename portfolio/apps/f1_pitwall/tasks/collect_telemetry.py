"""Celery task for bulk-creating telemetry snapshots during live sessions."""

import logging

from celery import shared_task
from django.db import transaction
from django.utils.dateparse import parse_datetime

from f1_pitwall.models import Driver, Session, TelemetrySnapshot

logger = logging.getLogger(__name__)


@shared_task
def collect_telemetry_snapshot(session_key, snapshots):
    """Persist telemetry snapshots passed by TelemetryEngine."""
    session = Session.objects.filter(session_key=session_key).first()
    if session is None or not snapshots:
        return {'created': 0}

    drivers = _drivers_map(snapshots)
    rows = _build_rows(session, drivers, snapshots)
    if not rows:
        return {'created': 0}

    with transaction.atomic():
        TelemetrySnapshot.objects.bulk_create(rows, batch_size=1000)
    return {'created': len(rows)}


def _drivers_map(snapshots):
    numbers = {row.get('driver_number') for row in snapshots}
    queryset = Driver.objects.filter(driver_number__in=numbers)
    return {d.driver_number: d for d in queryset}


def _build_rows(session, drivers, snapshots):
    rows = []
    for snap in snapshots:
        row = _build_row(session, drivers, snap)
        if row:
            rows.append(row)
    return rows


def _build_row(session, drivers, snap):
    driver = drivers.get(snap.get('driver_number'))
    timestamp = parse_datetime(snap.get('timestamp') or '')
    numeric = _numeric_fields(snap)
    if driver is None or timestamp is None or numeric is None:
        return None
    return TelemetrySnapshot(
        session=session,
        driver=driver,
        timestamp=timestamp,
        speed=numeric['speed'],
        rpm=numeric['rpm'],
        throttle=numeric['throttle'],
        brake=numeric['brake'],
        gear=numeric['gear'],
        drs=numeric['drs'],
        data_source=snap.get('data_source') or 'openf1_car_data',
        is_fallback=bool(snap.get('is_fallback')),
    )


def _numeric_fields(snap):
    fields = {}
    for key in ('speed', 'rpm', 'throttle', 'brake', 'gear', 'drs'):
        value = _to_int(snap.get(key), default=0)
        if value is None:
            logger.warning('Invalid telemetry field %s=%r; row skipped', key, snap.get(key))
            return None
        fields[key] = value
    return fields


def _to_int(value, default=0):
    if value in (None, ''):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
