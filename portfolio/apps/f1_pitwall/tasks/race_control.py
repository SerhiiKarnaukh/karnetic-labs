"""Celery task for broadcasting race control updates to websocket clients."""

import logging

from celery import shared_task
from django.utils.dateparse import parse_datetime

from f1_pitwall.exceptions import F1PitwallError
from f1_pitwall.services.race_control_service import RaceControlService

logger = logging.getLogger(__name__)


@shared_task
def broadcast_race_control(session_key, since_timestamp=None):
    """Fetch and broadcast new race control messages for a session."""
    service = RaceControlService()
    since = _parse_since_timestamp(since_timestamp)
    try:
        count = service.broadcast_new_messages(session_key, since)
    except F1PitwallError as exc:
        logger.warning(
            'broadcast_race_control skipped for session %s: %s',
            session_key,
            exc,
        )
        return {'broadcasted': 0}
    return {'broadcasted': count}


def _parse_since_timestamp(value):
    if value is None:
        return None
    if hasattr(value, 'tzinfo'):
        return value
    return parse_datetime(str(value))
