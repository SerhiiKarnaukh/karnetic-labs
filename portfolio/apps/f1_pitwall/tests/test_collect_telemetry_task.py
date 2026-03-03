"""Tests for collect_telemetry_snapshot Celery task."""

from django.test import TestCase

from f1_pitwall.models import Driver, Session, TelemetrySnapshot
from f1_pitwall.tasks.collect_telemetry import collect_telemetry_snapshot


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


def create_driver(driver_number):
    return Driver.objects.create(
        driver_number=driver_number,
        full_name=f'Driver {driver_number}',
        name_acronym=f'D{driver_number % 10}{driver_number % 10}',
        team_name='Team',
        team_colour='#123456',
    )


class CollectTelemetrySnapshotTaskTest(TestCase):
    """Task-level persistence behavior tests."""

    def setUp(self):
        self.session = create_session()
        self.driver = create_driver(1)

    def test_persists_valid_snapshots(self):
        payload = [{
            'driver_number': 1,
            'timestamp': '2024-03-02T15:00:01+00:00',
            'speed': 320,
            'rpm': 12000,
            'throttle': 99,
            'brake': 0,
            'gear': 8,
            'drs': 12,
        }]

        result = collect_telemetry_snapshot(self.session.session_key, payload)

        self.assertEqual(result['created'], 1)
        self.assertEqual(TelemetrySnapshot.objects.count(), 1)
        snap = TelemetrySnapshot.objects.first()
        self.assertEqual(snap.driver, self.driver)
        self.assertEqual(snap.speed, 320)

    def test_skips_unknown_driver_and_invalid_timestamp(self):
        payload = [
            {
                'driver_number': 999,
                'timestamp': '2024-03-02T15:00:01+00:00',
                'speed': 300,
            },
            {
                'driver_number': 1,
                'timestamp': 'invalid',
                'speed': 305,
            },
        ]

        result = collect_telemetry_snapshot(self.session.session_key, payload)

        self.assertEqual(result['created'], 0)
        self.assertEqual(TelemetrySnapshot.objects.count(), 0)

    def test_returns_zero_when_session_missing(self):
        payload = [{
            'driver_number': 1,
            'timestamp': '2024-03-02T15:00:01+00:00',
            'speed': 300,
        }]

        result = collect_telemetry_snapshot(999999, payload)

        self.assertEqual(result['created'], 0)
        self.assertEqual(TelemetrySnapshot.objects.count(), 0)
