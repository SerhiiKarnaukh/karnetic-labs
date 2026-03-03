"""Celery task for bulk-creating telemetry snapshots during live sessions."""

from celery import shared_task
from django.db import transaction
from django.utils.dateparse import parse_datetime

from f1_pitwall.models import Driver, Session, TelemetrySnapshot


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
    if driver is None or timestamp is None:
        return None
    return TelemetrySnapshot(
        session=session,
        driver=driver,
        timestamp=timestamp,
        speed=int(snap.get('speed') or 0),
        rpm=int(snap.get('rpm') or 0),
        throttle=int(snap.get('throttle') or 0),
        brake=int(snap.get('brake') or 0),
        gear=int(snap.get('gear') or 0),
        drs=int(snap.get('drs') or 0),
    )
