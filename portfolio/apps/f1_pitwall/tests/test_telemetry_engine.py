"""Tests for telemetry polling, broadcasting, and snapshot persistence."""

from unittest.mock import AsyncMock, MagicMock, patch

from django.test import TestCase

from f1_pitwall.models import Driver, Session, TelemetrySnapshot
from f1_pitwall.services.telemetry_engine import (
    STATUS_COMPLETE,
    STATUS_LIVE,
    STATUS_NOT_STARTED,
    TelemetryEngine,
)


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


def create_driver(driver_number, active=True):
    return Driver.objects.create(
        driver_number=driver_number,
        full_name=f'Driver {driver_number}',
        name_acronym=f'D{driver_number % 10}{driver_number % 10}',
        team_name='Team',
        team_colour='#123456',
        is_active=active,
    )


class TelemetryEngineStatusTest(TestCase):
    """Session lifecycle status tracking."""

    def test_session_status_lifecycle(self):
        engine = TelemetryEngine(
            client=MagicMock(), channel_layer=MagicMock(), persist_snapshots=False,
        )
        self.assertEqual(engine.get_session_status(9158), STATUS_NOT_STARTED)

        engine.start_live_session(9158)
        self.assertEqual(engine.get_session_status(9158), STATUS_LIVE)

        engine.stop_live_session(9158)
        self.assertEqual(engine.get_session_status(9158), STATUS_COMPLETE)


class TelemetryEnginePollingTest(TestCase):
    """Polling behavior and timestamp tracking."""

    def setUp(self):
        create_session()
        create_driver(1)

    def test_poll_telemetry_passes_since_timestamp(self):
        client = MagicMock()
        client.get_car_data = AsyncMock(return_value=[])
        layer = MagicMock()
        layer.group_send = AsyncMock()
        engine = TelemetryEngine(client=client, channel_layer=layer)

        engine.poll_telemetry(
            session_key=9158,
            driver_numbers=[1],
            since_timestamp='2024-03-02T15:00:00+00:00',
        )

        client.get_car_data.assert_awaited_once_with(
            session_key=9158,
            driver_number=1,
            date_gt='2024-03-02T15:00:00+00:00',
        )

    def test_snapshot_all_drivers_uses_only_active_drivers(self):
        create_driver(44, active=True)
        create_driver(99, active=False)

        async def _by_driver(session_key, driver_number, date_gt):
            if driver_number == 1:
                return [{'date': '2024-03-02T15:00:01+00:00', 'speed': 300}]
            if driver_number == 44:
                return [{'date': '2024-03-02T15:00:02+00:00', 'speed': 310}]
            return []

        client = MagicMock()
        client.get_car_data = AsyncMock(side_effect=_by_driver)
        layer = MagicMock()
        layer.group_send = AsyncMock()
        engine = TelemetryEngine(client=client, channel_layer=layer)

        snapshots = engine.snapshot_all_drivers(9158)

        called_drivers = [
            call.kwargs['driver_number']
            for call in client.get_car_data.await_args_list
        ]
        self.assertEqual(sorted(called_drivers), [1, 44])
        self.assertEqual(len(snapshots), 2)

    @patch('f1_pitwall.services.telemetry_engine.time.sleep')
    def test_run_polling_loop_respects_max_iterations(self, mock_sleep):
        client = MagicMock()
        client.get_car_data = AsyncMock(return_value=[])
        engine = TelemetryEngine(
            client=client,
            channel_layer=MagicMock(),
            persist_snapshots=False,
            poll_interval_seconds=0.01,
        )

        with patch.object(engine, 'poll_telemetry') as poll:
            engine.run_polling_loop(
                session_key=9158,
                driver_numbers=[1],
                max_iterations=3,
            )

        self.assertEqual(poll.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)


class TelemetryEnginePersistenceTest(TestCase):
    """Persistence and broadcasting behavior."""

    def setUp(self):
        self.session = create_session()
        self.driver = create_driver(1)

    def test_poll_persists_snapshot_and_broadcasts(self):
        client = MagicMock()
        client.get_car_data = AsyncMock(return_value=[{
            'date': '2024-03-02T15:00:01+00:00',
            'speed': 320,
            'rpm': 12000,
            'throttle': 98,
            'brake': 0,
            'n_gear': 8,
            'drs': 12,
        }])
        layer = MagicMock()
        layer.group_send = AsyncMock()
        engine = TelemetryEngine(client=client, channel_layer=layer)

        snapshots = engine.poll_telemetry(9158, [1])

        self.assertEqual(len(snapshots), 1)
        self.assertEqual(TelemetrySnapshot.objects.count(), 1)
        snap = TelemetrySnapshot.objects.first()
        self.assertEqual(snap.session, self.session)
        self.assertEqual(snap.driver, self.driver)
        self.assertEqual(snap.speed, 320)

        layer.group_send.assert_awaited_once()
        event = layer.group_send.await_args.args[1]
        self.assertEqual(event['type'], 'telemetry_message')
        self.assertEqual(event['data']['type'], 'telemetry')
        self.assertEqual(event['data']['driver'], 1)

    def test_poll_skips_rows_with_invalid_timestamp(self):
        client = MagicMock()
        client.get_car_data = AsyncMock(return_value=[{
            'date': 'invalid-date',
            'speed': 320,
        }])
        layer = MagicMock()
        layer.group_send = AsyncMock()
        engine = TelemetryEngine(client=client, channel_layer=layer)

        snapshots = engine.poll_telemetry(9158, [1])

        self.assertEqual(snapshots, [])
        self.assertEqual(TelemetrySnapshot.objects.count(), 0)
        layer.group_send.assert_not_awaited()

    def test_poll_does_not_persist_when_disabled(self):
        client = MagicMock()
        client.get_car_data = AsyncMock(return_value=[{
            'date': '2024-03-02T15:00:01+00:00',
            'speed': 305,
        }])
        layer = MagicMock()
        layer.group_send = AsyncMock()
        engine = TelemetryEngine(
            client=client,
            channel_layer=layer,
            persist_snapshots=False,
        )

        snapshots = engine.poll_telemetry(9158, [1])

        self.assertEqual(len(snapshots), 1)
        self.assertEqual(TelemetrySnapshot.objects.count(), 0)
        layer.group_send.assert_awaited_once()

    def test_poll_skips_persistence_when_session_missing(self):
        client = MagicMock()
        client.get_car_data = AsyncMock(return_value=[{
            'date': '2024-03-02T15:00:01+00:00',
            'speed': 305,
        }])
        layer = MagicMock()
        layer.group_send = AsyncMock()
        engine = TelemetryEngine(client=client, channel_layer=layer)

        engine.poll_telemetry(999999, [1])

        self.assertEqual(TelemetrySnapshot.objects.count(), 0)

    @patch('f1_pitwall.tasks.collect_telemetry.collect_telemetry_snapshot.delay')
    def test_poll_enqueues_celery_persistence_when_enabled(self, mock_delay):
        client = MagicMock()
        client.get_car_data = AsyncMock(return_value=[{
            'date': '2024-03-02T15:00:01+00:00',
            'speed': 315,
            'rpm': 11800,
            'throttle': 95,
            'brake': 1,
            'n_gear': 7,
            'drs': 10,
        }])
        layer = MagicMock()
        layer.group_send = AsyncMock()
        engine = TelemetryEngine(
            client=client,
            channel_layer=layer,
            use_celery_persistence=True,
        )

        engine.poll_telemetry(9158, [1])

        mock_delay.assert_called_once()
        self.assertEqual(TelemetrySnapshot.objects.count(), 0)
