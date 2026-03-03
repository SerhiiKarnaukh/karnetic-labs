"""Tests for broadcast_race_control Celery task."""

from datetime import datetime, timezone as dt_timezone
from unittest.mock import MagicMock, patch

from django.test import TestCase

from f1_pitwall.exceptions import OpenF1ConnectionError
from f1_pitwall.tasks.race_control import broadcast_race_control


class BroadcastRaceControlTaskTest(TestCase):
    """Task behavior: success path, timestamp parsing, and failure fallback."""

    @patch('f1_pitwall.tasks.race_control.RaceControlService')
    def test_broadcast_task_calls_service_with_parsed_timestamp(
        self, mock_service_cls,
    ):
        service = MagicMock()
        service.broadcast_new_messages.return_value = 3
        mock_service_cls.return_value = service

        result = broadcast_race_control(
            session_key=9158,
            since_timestamp='2024-03-02T15:00:00+00:00',
        )

        expected_since = datetime(2024, 3, 2, 15, 0, 0, tzinfo=dt_timezone.utc)
        service.broadcast_new_messages.assert_called_once_with(9158, expected_since)
        self.assertEqual(result, {'broadcasted': 3})

    @patch('f1_pitwall.tasks.race_control.RaceControlService')
    def test_broadcast_task_accepts_none_timestamp(self, mock_service_cls):
        service = MagicMock()
        service.broadcast_new_messages.return_value = 2
        mock_service_cls.return_value = service

        result = broadcast_race_control(session_key=9158, since_timestamp=None)

        service.broadcast_new_messages.assert_called_once_with(9158, None)
        self.assertEqual(result, {'broadcasted': 2})

    @patch('f1_pitwall.tasks.race_control.RaceControlService')
    def test_broadcast_task_handles_openf1_failures(self, mock_service_cls):
        service = MagicMock()
        service.broadcast_new_messages.side_effect = OpenF1ConnectionError('down')
        mock_service_cls.return_value = service

        result = broadcast_race_control(
            session_key=9158,
            since_timestamp='2024-03-02T15:00:00+00:00',
        )

        self.assertEqual(result, {'broadcasted': 0})
