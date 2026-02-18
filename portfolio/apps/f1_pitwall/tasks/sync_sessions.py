"""Celery task for periodic session and driver metadata synchronization."""

import logging

from celery import shared_task

from f1_pitwall.exceptions import F1PitwallError
from f1_pitwall.services.session_sync import SessionSyncService

logger = logging.getLogger(__name__)

EMPTY_RESULT = {'created': 0, 'updated': 0}


@shared_task
def sync_f1_sessions(year=None):
    """Pull session and driver metadata from OpenF1, update local DB.

    Scheduled every 6 hours via Celery Beat.
    Gracefully handles API unavailability during live F1 sessions.
    """
    service = SessionSyncService()

    session_result = _sync_step(
        'sessions', service.sync_sessions, year=year,
    )
    driver_result = _sync_step(
        'drivers', service.sync_drivers,
    )

    summary = (
        f"Sessions: {session_result['created']} created, "
        f"{session_result['updated']} updated | "
        f"Drivers: {driver_result['created']} created, "
        f"{driver_result['updated']} updated"
    )
    logger.info("sync_f1_sessions complete: %s", summary)
    return summary


def _sync_step(name, func, **kwargs):
    """Execute a sync step, returning empty result on API failure."""
    try:
        return func(**kwargs)
    except F1PitwallError as exc:
        logger.warning(
            "Sync %s skipped — OpenF1 API unavailable: %s", name, exc,
        )
        return EMPTY_RESULT
