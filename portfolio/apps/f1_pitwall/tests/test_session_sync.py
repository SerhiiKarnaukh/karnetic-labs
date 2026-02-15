"""Tests for session and driver synchronization from OpenF1."""

from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from f1_pitwall.models import Driver, Session
from f1_pitwall.services.session_sync import SessionSyncService


MOCK_SESSIONS = [
    {
        'session_key': 9158,
        'session_type': 'Practice',
        'session_name': 'Practice 1',
        'date_start': '2023-09-15T09:30:00+00:00',
        'date_end': '2023-09-15T10:30:00+00:00',
        'meeting_key': 1219,
        'circuit_short_name': 'Singapore',
        'country_code': 'SGP',
        'country_name': 'Singapore',
        'location': 'Marina Bay',
        'year': 2023,
    },
    {
        'session_key': 9159,
        'session_type': 'Race',
        'session_name': 'Race',
        'date_start': '2023-09-17T12:00:00+00:00',
        'date_end': '2023-09-17T14:00:00+00:00',
        'meeting_key': 1219,
        'circuit_short_name': 'Singapore',
        'country_code': 'SGP',
        'country_name': 'Singapore',
        'location': 'Marina Bay',
        'year': 2023,
    },
]

MOCK_DRIVERS = [
    {
        'driver_number': 1,
        'full_name': 'Max VERSTAPPEN',
        'name_acronym': 'VER',
        'team_name': 'Red Bull Racing',
        'team_colour': '3671C6',
        'headshot_url': 'https://example.com/ver.png',
        'country_code': 'NED',
    },
    {
        'driver_number': 44,
        'full_name': 'Lewis HAMILTON',
        'name_acronym': 'HAM',
        'team_name': 'Mercedes',
        'team_colour': '6CD3BF',
        'headshot_url': None,
        'country_code': 'GBR',
    },
]


class SyncSessionsTest(TestCase):
    """Tests for sync_sessions()."""

    @patch.object(SessionSyncService, '_fetch_sessions', return_value=MOCK_SESSIONS)
    def test_creates_new_sessions(self, mock_fetch):
        service = SessionSyncService()
        result = service.sync_sessions(year=2023)

        self.assertEqual(result['created'], 2)
        self.assertEqual(result['updated'], 0)
        self.assertEqual(Session.objects.count(), 2)

    @patch.object(SessionSyncService, '_fetch_sessions', return_value=MOCK_SESSIONS)
    def test_maps_fields_correctly(self, mock_fetch):
        service = SessionSyncService()
        service.sync_sessions()

        session = Session.objects.get(session_key=9158)
        self.assertEqual(session.session_name, 'Practice 1')
        self.assertEqual(session.session_type, 'practice')
        self.assertEqual(session.circuit_name, 'Marina Bay')
        self.assertEqual(session.circuit_short_name, 'Singapore')
        self.assertEqual(session.country_code, 'SGP')
        self.assertEqual(session.year, 2023)
        self.assertEqual(session.meeting_key, 1219)

    @patch.object(SessionSyncService, '_fetch_sessions', return_value=MOCK_SESSIONS)
    def test_maps_race_session_type(self, mock_fetch):
        service = SessionSyncService()
        service.sync_sessions()

        race = Session.objects.get(session_key=9159)
        self.assertEqual(race.session_type, 'race')

    @patch.object(SessionSyncService, '_fetch_sessions', return_value=MOCK_SESSIONS)
    def test_updates_existing_sessions(self, mock_fetch):
        Session.objects.create(
            session_key=9158,
            meeting_key=0,
            session_name='Old Name',
            session_type='practice',
            circuit_name='',
            circuit_short_name='',
            country_name='',
            country_code='',
            date_start='2023-09-15T09:30:00Z',
            year=2023,
        )

        service = SessionSyncService()
        result = service.sync_sessions()

        self.assertEqual(result['created'], 1)
        self.assertEqual(result['updated'], 1)

        updated = Session.objects.get(session_key=9158)
        self.assertEqual(updated.session_name, 'Practice 1')
        self.assertEqual(updated.circuit_name, 'Marina Bay')

    @patch.object(SessionSyncService, '_fetch_sessions', return_value=[])
    def test_empty_api_response(self, mock_fetch):
        service = SessionSyncService()
        result = service.sync_sessions()

        self.assertEqual(result['created'], 0)
        self.assertEqual(result['updated'], 0)

    @patch.object(SessionSyncService, '_fetch_sessions', return_value=MOCK_SESSIONS)
    def test_passes_year_to_fetch(self, mock_fetch):
        service = SessionSyncService()
        service.sync_sessions(year=2024)

        mock_fetch.assert_called_once_with(2024)

    @patch.object(SessionSyncService, '_fetch_sessions', return_value=[{'no_key': True}])
    def test_skips_entry_without_session_key(self, mock_fetch):
        service = SessionSyncService()
        result = service.sync_sessions()

        self.assertEqual(result['created'], 0)
        self.assertEqual(Session.objects.count(), 0)


class SyncDriversTest(TestCase):
    """Tests for sync_drivers()."""

    @patch.object(SessionSyncService, '_fetch_drivers', return_value=MOCK_DRIVERS)
    def test_creates_new_drivers(self, mock_fetch):
        service = SessionSyncService()
        result = service.sync_drivers()

        self.assertEqual(result['created'], 2)
        self.assertEqual(result['updated'], 0)
        self.assertEqual(Driver.objects.count(), 2)

    @patch.object(SessionSyncService, '_fetch_drivers', return_value=MOCK_DRIVERS)
    def test_maps_fields_correctly(self, mock_fetch):
        service = SessionSyncService()
        service.sync_drivers()

        ver = Driver.objects.get(driver_number=1)
        self.assertEqual(ver.full_name, 'Max VERSTAPPEN')
        self.assertEqual(ver.name_acronym, 'VER')
        self.assertEqual(ver.team_name, 'Red Bull Racing')
        self.assertEqual(ver.team_colour, '#3671C6')
        self.assertEqual(ver.country_code, 'NED')
        self.assertTrue(ver.is_active)

    @patch.object(SessionSyncService, '_fetch_drivers', return_value=MOCK_DRIVERS)
    def test_prefixes_hash_to_team_colour(self, mock_fetch):
        service = SessionSyncService()
        service.sync_drivers()

        ham = Driver.objects.get(driver_number=44)
        self.assertEqual(ham.team_colour, '#6CD3BF')

    @patch.object(SessionSyncService, '_fetch_drivers', return_value=MOCK_DRIVERS)
    def test_handles_null_headshot_url(self, mock_fetch):
        service = SessionSyncService()
        service.sync_drivers()

        ham = Driver.objects.get(driver_number=44)
        self.assertEqual(ham.headshot_url, '')

    @patch.object(SessionSyncService, '_fetch_drivers', return_value=MOCK_DRIVERS)
    def test_updates_existing_drivers(self, mock_fetch):
        Driver.objects.create(
            driver_number=1,
            full_name='Old Name',
            name_acronym='OLD',
            team_name='Old Team',
            team_colour='#000000',
        )

        service = SessionSyncService()
        result = service.sync_drivers()

        self.assertEqual(result['created'], 1)
        self.assertEqual(result['updated'], 1)

        ver = Driver.objects.get(driver_number=1)
        self.assertEqual(ver.full_name, 'Max VERSTAPPEN')
        self.assertEqual(ver.team_name, 'Red Bull Racing')

    @patch.object(SessionSyncService, '_fetch_drivers', return_value=[{'no_number': True}])
    def test_skips_entry_without_driver_number(self, mock_fetch):
        service = SessionSyncService()
        result = service.sync_drivers()

        self.assertEqual(result['created'], 0)
        self.assertEqual(Driver.objects.count(), 0)


class SessionTypeMapTest(TestCase):
    """Tests for session type mapping edge cases."""

    @patch.object(SessionSyncService, '_fetch_sessions')
    def test_maps_sprint_qualifying(self, mock_fetch):
        mock_fetch.return_value = [{
            **MOCK_SESSIONS[0],
            'session_key': 5000,
            'session_type': 'Sprint Qualifying',
        }]

        service = SessionSyncService()
        service.sync_sessions()

        session = Session.objects.get(session_key=5000)
        self.assertEqual(session.session_type, 'qualifying')

    @patch.object(SessionSyncService, '_fetch_sessions')
    def test_maps_sprint_shootout(self, mock_fetch):
        mock_fetch.return_value = [{
            **MOCK_SESSIONS[0],
            'session_key': 5001,
            'session_type': 'Sprint Shootout',
        }]

        service = SessionSyncService()
        service.sync_sessions()

        session = Session.objects.get(session_key=5001)
        self.assertEqual(session.session_type, 'qualifying')

    @patch.object(SessionSyncService, '_fetch_sessions')
    def test_unknown_type_defaults_to_practice(self, mock_fetch):
        mock_fetch.return_value = [{
            **MOCK_SESSIONS[0],
            'session_key': 5002,
            'session_type': 'Unknown Session',
        }]

        service = SessionSyncService()
        service.sync_sessions()

        session = Session.objects.get(session_key=5002)
        self.assertEqual(session.session_type, 'practice')


class GetAvailableSessionsTest(TestCase):
    """Tests for get_available_sessions()."""

    def setUp(self):
        Session.objects.create(
            session_key=100, meeting_key=1, session_name='Race',
            session_type='race', circuit_name='Test', circuit_short_name='TST',
            country_name='Test', country_code='TST',
            date_start='2024-03-02T15:00:00Z', year=2024,
        )
        Session.objects.create(
            session_key=101, meeting_key=1, session_name='Practice 1',
            session_type='practice', circuit_name='Test',
            circuit_short_name='TST', country_name='Test', country_code='TST',
            date_start='2024-03-01T10:00:00Z', year=2024,
        )
        Session.objects.create(
            session_key=200, meeting_key=2, session_name='Race',
            session_type='race', circuit_name='Other',
            circuit_short_name='OTH', country_name='Other', country_code='OTH',
            date_start='2023-06-15T14:00:00Z', year=2023,
        )

    def test_filters_by_year(self):
        service = SessionSyncService()
        result = service.get_available_sessions(year=2024)
        self.assertEqual(result.count(), 2)

    def test_filters_by_year_and_type(self):
        service = SessionSyncService()
        result = service.get_available_sessions(year=2024, session_type='race')
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first().session_key, 100)

    def test_returns_empty_for_nonexistent_year(self):
        service = SessionSyncService()
        result = service.get_available_sessions(year=2025)
        self.assertEqual(result.count(), 0)


class DetectLiveSessionTest(TestCase):
    """Tests for detect_live_session()."""

    def test_returns_none_when_no_live_session(self):
        service = SessionSyncService()
        self.assertIsNone(service.detect_live_session())

    def test_returns_live_session(self):
        now = timezone.now()
        Session.objects.create(
            session_key=999, meeting_key=1, session_name='Race',
            session_type='race', circuit_name='Test', circuit_short_name='TST',
            country_name='Test', country_code='TST',
            date_start=now - timezone.timedelta(hours=1),
            date_end=now + timezone.timedelta(hours=1),
            year=2024, is_live=True,
        )

        service = SessionSyncService()
        result = service.detect_live_session()
        self.assertIsNotNone(result)
        self.assertEqual(result.session_key, 999)

    def test_ignores_non_live_session_within_time_window(self):
        now = timezone.now()
        Session.objects.create(
            session_key=998, meeting_key=1, session_name='Race',
            session_type='race', circuit_name='Test', circuit_short_name='TST',
            country_name='Test', country_code='TST',
            date_start=now - timezone.timedelta(hours=1),
            date_end=now + timezone.timedelta(hours=1),
            year=2024, is_live=False,
        )

        service = SessionSyncService()
        self.assertIsNone(service.detect_live_session())
