"""Celery task for periodic session and driver metadata synchronization."""

import logging

from celery import shared_task

from f1_pitwall.services.session_sync import SessionSyncService

logger = logging.getLogger(__name__)


@shared_task
def sync_f1_sessions(year=None):
    """Pull session and driver metadata from OpenF1, update local DB.

    Scheduled every 6 hours via Celery Beat.
    Can also be called manually or from the management command.
    """
    service = SessionSyncService()

    session_result = service.sync_sessions(year=year)
    driver_result = service.sync_drivers()

    summary = (
        f"Sessions: {session_result['created']} created, "
        f"{session_result['updated']} updated | "
        f"Drivers: {driver_result['created']} created, "
        f"{driver_result['updated']} updated"
    )
    logger.info("sync_f1_sessions complete: %s", summary)
    return summary
