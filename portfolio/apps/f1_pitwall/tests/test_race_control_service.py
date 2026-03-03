"""Tests for RaceControlService fetching, parsing, and broadcasting."""

from datetime import datetime, timezone as dt_timezone
from unittest.mock import AsyncMock, MagicMock

from django.test import TestCase
from django.utils import timezone

from f1_pitwall.exceptions import OpenF1ConnectionError
from f1_pitwall.models import RaceControlMessage, Session
from f1_pitwall.services.race_control_service import RaceControlService


def create_session(session_key=9158):
    return Session.objects.create(
        session_key=session_key,
        meeting_key=1219,
        session_name='Race',
        session_type='race',
        circuit_name='Bahrain International Circuit',
        circuit_short_name='Bahrain',
        country_name='Bahrain',
        country_code='BHR',
        date_start='2024-03-02T15:00:00Z',
        year=2024,
    )


class RaceControlServiceTest(TestCase):
    """Covers core service methods from Section 3.5."""

    def setUp(self):
        self.session = create_session()
        self.raw_messages = [
            {
                'date': '2024-03-02T15:01:00+00:00',
                'category': 'Flag',
                'message': 'Yellow flag in sector 2',
                'flag': 'YELLOW',
                'driver_number': None,
                'lap_number': 3,
                'sector': 2,
            },
            {
                'date': '2024-03-02T15:02:00+00:00',
                'category': 'SafetyCar',
                'message': 'SAFETY CAR DEPLOYED',
                'flag': '',
                'driver_number': None,
                'lap_number': 4,
                'sector': None,
            },
            {
                'date': '2024-03-02T15:03:00+00:00',
                'category': 'Flag',
                'message': 'Green flag',
                'flag': 'GREEN',
                'driver_number': None,
                'lap_number': 5,
                'sector': 2,
            },
        ]

    def _service(self, messages=None):
        client = MagicMock()
        client.get_race_control = AsyncMock(return_value=messages or self.raw_messages)
        layer = MagicMock()
        layer.group_send = AsyncMock()
        return RaceControlService(client=client, channel_layer=layer), client, layer

    def test_get_messages_persists_rows(self):
        service, client, _ = self._service()

        queryset = service.get_messages(self.session.session_key)

        self.assertEqual(queryset.count(), 3)
        self.assertEqual(RaceControlMessage.objects.count(), 3)
        client.get_race_control.assert_awaited_once_with(self.session.session_key)

    def test_get_latest_flag_returns_latest_non_empty(self):
        service, _, _ = self._service()

        latest_flag = service.get_latest_flag(self.session.session_key)

        self.assertEqual(latest_flag, 'GREEN')

    def test_is_safety_car_active_true(self):
        service, _, _ = self._service(messages=[{
            'date': '2024-03-02T15:02:00+00:00',
            'category': 'SafetyCar',
            'message': 'SAFETY CAR DEPLOYED',
            'flag': '',
        }])

        self.assertTrue(service.is_safety_car_active(self.session.session_key))

    def test_is_safety_car_active_false_when_ending_message(self):
        service, _, _ = self._service(messages=[{
            'date': '2024-03-02T15:02:00+00:00',
            'category': 'SafetyCar',
            'message': 'SAFETY CAR ENDING',
            'flag': '',
        }])

        self.assertFalse(service.is_safety_car_active(self.session.session_key))

    def test_broadcast_new_messages_filters_by_since_timestamp(self):
        service, _, layer = self._service()
        since = datetime(2024, 3, 2, 15, 1, 30, tzinfo=dt_timezone.utc)

        count = service.broadcast_new_messages(self.session.session_key, since)

        self.assertEqual(count, 2)
        self.assertEqual(layer.group_send.await_count, 2)

    def test_broadcast_new_messages_avoids_duplicate_rebroadcast(self):
        service, _, layer = self._service()
        since = datetime(2024, 3, 2, 15, 0, 0, tzinfo=dt_timezone.utc)

        first = service.broadcast_new_messages(self.session.session_key, since)
        second = service.broadcast_new_messages(self.session.session_key, since)

        self.assertEqual(first, 3)
        self.assertEqual(second, 0)
        self.assertEqual(layer.group_send.await_count, 3)

    def test_unknown_session_returns_empty_without_crash(self):
        service, client, _ = self._service()

        queryset = service.get_messages(999999)
        broadcasted = service.broadcast_new_messages(999999, timezone.now())

        self.assertEqual(queryset.count(), 0)
        self.assertEqual(broadcasted, 0)
        client.get_race_control.assert_not_awaited()

    def test_fetch_failure_returns_existing_data_without_crash(self):
        client = MagicMock()
        client.get_race_control = AsyncMock(
            side_effect=OpenF1ConnectionError('OpenF1 down'),
        )
        layer = MagicMock()
        layer.group_send = AsyncMock()
        service = RaceControlService(client=client, channel_layer=layer)

        existing = RaceControlMessage.objects.create(
            session=self.session,
            timestamp='2024-03-02T15:00:00Z',
            category='Flag',
            message='Existing message',
            flag='YELLOW',
        )

        queryset = service.get_messages(self.session.session_key)
        latest_flag = service.get_latest_flag(self.session.session_key)
        broadcasted = service.broadcast_new_messages(
            self.session.session_key, timezone.now(),
        )

        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().id, existing.id)
        self.assertEqual(latest_flag, 'YELLOW')
        self.assertEqual(broadcasted, 0)
