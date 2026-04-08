"""Tests for on-demand endpoint hydration from OpenF1."""

from datetime import timedelta
from unittest.mock import AsyncMock, Mock

from django.test import TestCase, override_settings
from django.utils import timezone

from f1_pitwall.exceptions import OpenF1APIError
from f1_pitwall.models import Driver, LapData, Session, TelemetrySnapshot
from f1_pitwall.services.session_data_hydrator import SessionDataHydrator


def create_session(session_key=9858):
    return Session.objects.create(
        session_key=session_key,
        meeting_key=1219,
        session_name='Race',
        session_type='race',
        circuit_name='Las Vegas Strip Circuit',
        circuit_short_name='Vegas',
        country_name='United States',
        country_code='USA',
        date_start=timezone.now() - timedelta(hours=3),
        date_end=timezone.now() - timedelta(hours=1),
        year=2025,
    )


def create_driver(driver_number=1, is_active=True):
    return Driver.objects.create(
        driver_number=driver_number,
        full_name='Driver Test',
        name_acronym='TST',
        team_name='Test Team',
        team_colour='#123456',
        is_active=is_active,
    )


class SessionDataHydratorLapTest(TestCase):
    @override_settings(F1_AUTO_HYDRATE_READ=True)
    def test_ensure_laps_upserts_missing_rows(self):
        session = create_session()
        driver = create_driver(1)
        client = Mock()
        client.get_lap_data = AsyncMock(return_value=[{
            'driver_number': 1,
            'lap_number': 3,
            'lap_duration': 90.111,
            'duration_sector_1': 28.0,
            'duration_sector_2': 34.0,
            'duration_sector_3': 28.1,
            'st_speed': 320.5,
            'is_pit_out_lap': 0,
            'is_pit_in_lap': 0,
            'is_personal_best': 1,
        }])

        SessionDataHydrator(client=client).ensure_laps(session)

        lap = LapData.objects.get(session=session, driver=driver, lap_number=3)
        self.assertEqual(lap.lap_duration, 90.111)
        self.assertEqual(lap.speed_trap, 320.5)
        self.assertTrue(lap.is_personal_best)

    @override_settings(F1_AUTO_HYDRATE_READ=False)
    def test_ensure_laps_skips_when_disabled(self):
        session = create_session()
        client = Mock()
        client.get_lap_data = AsyncMock(return_value=[])

        SessionDataHydrator(client=client).ensure_laps(session)

        self.assertEqual(LapData.objects.count(), 0)
        client.get_lap_data.assert_not_awaited()

    @override_settings(F1_AUTO_HYDRATE_READ=True)
    def test_ensure_laps_handles_openf1_error(self):
        session = create_session()
        client = Mock()
        client.get_lap_data = AsyncMock(side_effect=OpenF1APIError('down'))

        SessionDataHydrator(client=client).ensure_laps(session)

        self.assertEqual(LapData.objects.count(), 0)


class SessionDataHydratorTelemetryTest(TestCase):
    @override_settings(F1_AUTO_HYDRATE_READ=True)
    def test_ensure_latest_snapshots_stores_latest_per_driver(self):
        session = create_session(session_key=9920)
        create_driver(1)
        client = Mock()
        client.get_car_data = AsyncMock(return_value=[
            {
                'date': '2025-11-23T05:26:00+00:00',
                'speed': 300,
                'rpm': 11000,
                'throttle': 90,
                'brake': 0,
                'n_gear': 7,
                'drs': 10,
            },
            {
                'date': '2025-11-23T05:26:10+00:00',
                'speed': 305,
                'rpm': 11200,
                'throttle': 92,
                'brake': 0,
                'n_gear': 8,
                'drs': 12,
            },
        ])

        SessionDataHydrator(client=client).ensure_latest_snapshots(session, 1)

        snapshot = TelemetrySnapshot.objects.get(
            session=session,
            driver__driver_number=1,
        )
        self.assertEqual(snapshot.speed, 305)
        self.assertEqual(snapshot.gear, 8)
        self.assertEqual(snapshot.data_source, 'openf1_car_data')
        self.assertFalse(snapshot.is_fallback)

    @override_settings(F1_AUTO_HYDRATE_READ=False)
    def test_ensure_latest_snapshots_skips_when_disabled(self):
        session = create_session(session_key=9947)
        create_driver(1)
        client = Mock()
        client.get_car_data = AsyncMock(return_value=[])

        SessionDataHydrator(client=client).ensure_latest_snapshots(session)

        self.assertEqual(TelemetrySnapshot.objects.count(), 0)
        client.get_car_data.assert_not_awaited()

    @override_settings(F1_AUTO_HYDRATE_READ=True)
    def test_ensure_latest_snapshots_falls_back_to_lap_speed_trap(self):
        session = create_session(session_key=9858)
        driver = create_driver(16)
        LapData.objects.create(
            session=session,
            driver=driver,
            lap_number=20,
            lap_duration=91.0,
            speed_trap=312.4,
        )
        client = Mock()
        client.get_car_data = AsyncMock(side_effect=OpenF1APIError('down'))

        SessionDataHydrator(client=client).ensure_latest_snapshots(session, 16)

        snapshot = TelemetrySnapshot.objects.get(
            session=session,
            driver__driver_number=16,
        )
        self.assertEqual(snapshot.speed, 312)
        self.assertEqual(snapshot.data_source, 'fallback_lap_speed_trap')
        self.assertTrue(snapshot.is_fallback)
