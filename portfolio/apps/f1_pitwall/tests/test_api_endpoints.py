"""Tests for basic REST API endpoints: sessions and drivers."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch

from f1_pitwall.models import (
    Driver,
    F1UserProfile,
    LapData,
    RaceControlMessage,
    Session,
    Stint,
    TelemetrySnapshot,
    WeatherData,
)

User = get_user_model()


def create_test_user(email='test@example.com', password='testpass123'):
    """Create and return a test user."""
    return User.objects.create_user(
        first_name='Test',
        last_name='User',
        username='testuser',
        email=email,
        password=password,
    )


def create_session(**overrides):
    """Create and return a test session with sensible defaults."""
    defaults = {
        'session_key': 9158,
        'meeting_key': 1219,
        'session_name': 'Race',
        'session_type': 'race',
        'circuit_name': 'Bahrain International Circuit',
        'circuit_short_name': 'Bahrain',
        'country_name': 'Bahrain',
        'country_code': 'BHR',
        'date_start': '2024-03-02T15:00:00Z',
        'year': 2024,
    }
    defaults.update(overrides)
    return Session.objects.create(**defaults)


def create_driver(**overrides):
    """Create and return a test driver with sensible defaults."""
    defaults = {
        'driver_number': 1,
        'full_name': 'Max VERSTAPPEN',
        'name_acronym': 'VER',
        'team_name': 'Red Bull Racing',
        'team_colour': '#3671C6',
    }
    defaults.update(overrides)
    return Driver.objects.create(**defaults)


def create_telemetry(session, driver, timestamp, **overrides):
    defaults = {
        'session': session,
        'driver': driver,
        'timestamp': timestamp,
        'speed': 300,
        'rpm': 11000,
        'throttle': 90,
        'brake': 0,
        'gear': 7,
        'drs': 10,
    }
    defaults.update(overrides)
    return TelemetrySnapshot.objects.create(**defaults)


def create_lap(session, driver, lap_number, **overrides):
    defaults = {
        'session': session,
        'driver': driver,
        'lap_number': lap_number,
        'lap_duration': 90.5,
        'sector_1': 28.1,
        'sector_2': 35.2,
        'sector_3': 27.2,
        'speed_trap': 325.0,
    }
    defaults.update(overrides)
    return LapData.objects.create(**defaults)


def create_weather(session, timestamp, **overrides):
    defaults = {
        'session': session,
        'timestamp': timestamp,
        'air_temperature': 29.0,
        'track_temperature': 35.0,
        'humidity': 60.0,
        'wind_speed': 3.0,
        'wind_direction': 120,
        'rainfall': False,
        'pressure': 1012.0,
    }
    defaults.update(overrides)
    return WeatherData.objects.create(**defaults)


def create_stint(session, driver, stint_number, **overrides):
    defaults = {
        'session': session,
        'driver': driver,
        'stint_number': stint_number,
        'compound': 'SOFT',
        'tyre_age_at_start': 0,
        'lap_start': 1,
        'lap_end': 10,
    }
    defaults.update(overrides)
    return Stint.objects.create(**defaults)


def create_race_control(session, timestamp, **overrides):
    defaults = {
        'session': session,
        'timestamp': timestamp,
        'category': 'Flag',
        'message': 'Green flag',
        'flag': 'GREEN',
        'driver_number': None,
        'lap_number': None,
        'sector': None,
    }
    defaults.update(overrides)
    return RaceControlMessage.objects.create(**defaults)


class F1RegisterViewTest(TestCase):
    """Tests for POST /f1/api/register/."""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('f1_pitwall:register')

    @patch('f1_pitwall.views.auth.send_activation_email')
    def test_register_creates_user_and_f1_profile(self, mock_send_email):
        payload = {
            'email': 'newf1@example.com',
            'username': 'newf1',
            'password': 'f1strongpass123',
            'first_name': 'New',
            'last_name': 'User',
        }

        res = self.client.post(self.url, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email='newf1@example.com')
        profile = F1UserProfile.objects.get(user=user)
        self.assertEqual(profile.role, F1UserProfile.Role.VIEWER)
        mock_send_email.assert_called_once()

    @patch('f1_pitwall.views.auth.send_activation_email')
    def test_duplicate_email_creates_f1_profile_when_user_has_none(
            self, mock_send_email,
    ):
        """Existing Account without F1UserProfile gets a profile on duplicate-email register."""
        create_test_user(email='duplicate@example.com')
        payload = {
            'email': 'duplicate@example.com',
            'username': 'duplicate',
            'password': 'f1strongpass123',
            'first_name': 'Dup',
            'last_name': 'User',
        }

        res = self.client.post(self.url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data.get('detail'), 'f1_profile_created')
        self.assertEqual(
            User.objects.filter(email='duplicate@example.com').count(), 1,
        )
        self.assertEqual(F1UserProfile.objects.count(), 1)
        mock_send_email.assert_not_called()

    def test_register_rejects_duplicate_email_when_f1_profile_exists(self):
        user = create_test_user(email='dupf1@example.com')
        F1UserProfile.objects.create(user=user)
        payload = {
            'email': 'dupf1@example.com',
            'username': 'other',
            'password': 'f1strongpass123',
            'first_name': 'X',
            'last_name': 'Y',
        }

        res = self.client.post(self.url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(F1UserProfile.objects.count(), 1)


class F1TokenObtainPairViewTest(TestCase):
    """Tests for POST /f1/api/v1/token/."""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('f1_pitwall:token-obtain-pair')

    def test_no_f1_profile_returns_400(self):
        user = create_test_user(email='notf1@example.com')
        user.is_active = True
        user.save(update_fields=['is_active'])

        res = self.client.post(
            self.url,
            {'email': 'notf1@example.com', 'password': 'testpass123'},
            format='json',
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data.get('error'), 'User profile does not exist.')

    def test_with_f1_profile_returns_tokens(self):
        user = create_test_user(email='hastoken@example.com')
        user.is_active = True
        user.save(update_fields=['is_active'])
        F1UserProfile.objects.create(user=user)

        res = self.client.post(
            self.url,
            {'email': 'hastoken@example.com', 'password': 'testpass123'},
            format='json',
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)


class F1MeViewTest(TestCase):
    """Tests for GET /f1/api/me/."""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('f1_pitwall:me')

    def test_unauthenticated_request_rejected(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_user_and_role(self):
        user = create_test_user(email='f1me@example.com')
        F1UserProfile.objects.create(user=user, role=F1UserProfile.Role.ENGINEER)

        self.client.force_authenticate(user)
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['email'], 'f1me@example.com')
        self.assertEqual(res.data['role'], F1UserProfile.Role.ENGINEER)

    def test_missing_f1_profile_returns_404(self):
        user = create_test_user(email='nof1@example.com')

        self.client.force_authenticate(user)
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            res.data.get('message'),
            'Profile does not exist for this user',
        )
        self.assertFalse(F1UserProfile.objects.filter(user=user).exists())


class SessionListViewTest(TestCase):
    """Tests for GET /f1/api/sessions/."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user()
        self.url = reverse('f1_pitwall:session-list')

    def test_unauthenticated_request_rejected(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_sessions(self):
        create_session(session_key=100)
        create_session(session_key=101, session_name='Practice 1',
                       session_type='practice')

        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_filter_by_year(self):
        create_session(session_key=100, year=2024)
        create_session(session_key=200, year=2023)

        self.client.force_authenticate(self.user)
        res = self.client.get(self.url, {'year': 2024})

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['session_key'], 100)

    def test_filter_by_type(self):
        create_session(session_key=100, session_type='race')
        create_session(session_key=101, session_type='practice')

        self.client.force_authenticate(self.user)
        res = self.client.get(self.url, {'type': 'race'})

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['session_key'], 100)

    def test_filter_by_circuit(self):
        create_session(session_key=100, circuit_short_name='Bahrain')
        create_session(session_key=101, circuit_short_name='Monza')

        self.client.force_authenticate(self.user)
        res = self.client.get(self.url, {'circuit': 'bah'})

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['session_key'], 100)

    def test_empty_list_returns_200(self):
        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 0)

    def test_sessions_ordered_by_date_desc(self):
        create_session(session_key=100, date_start='2024-03-02T15:00:00Z')
        create_session(session_key=101, date_start='2024-06-10T14:00:00Z')

        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)

        self.assertEqual(res.data[0]['session_key'], 101)
        self.assertEqual(res.data[1]['session_key'], 100)


class SessionDetailViewTest(TestCase):
    """Tests for GET /f1/api/sessions/<session_key>/."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user()

    def test_unauthenticated_request_rejected(self):
        session = create_session()
        url = reverse(
            'f1_pitwall:session-detail',
            kwargs={'session_key': session.session_key},
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_session_detail(self):
        session = create_session()
        url = reverse(
            'f1_pitwall:session-detail',
            kwargs={'session_key': session.session_key},
        )

        self.client.force_authenticate(self.user)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['session_key'], session.session_key)
        self.assertEqual(
            res.data['circuit_name'], 'Bahrain International Circuit',
        )
        self.assertIn('meeting_key', res.data)
        self.assertIn('created_at', res.data)

    def test_nonexistent_session_returns_404(self):
        url = reverse(
            'f1_pitwall:session-detail',
            kwargs={'session_key': 99999},
        )

        self.client.force_authenticate(self.user)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


class SessionLiveViewTest(TestCase):
    """Tests for GET /f1/api/sessions/live/."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user()
        self.url = reverse('f1_pitwall:session-live')

    def test_unauthenticated_request_rejected(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_no_live_session(self):
        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('detail', res.data)

    def test_returns_live_session(self):
        create_session(session_key=100, is_live=True)
        create_session(session_key=101, is_live=False)

        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['session_key'], 100)
        self.assertTrue(res.data['is_live'])


class DriverListViewTest(TestCase):
    """Tests for GET /f1/api/drivers/."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user()
        self.url = reverse('f1_pitwall:driver-list')

    def test_unauthenticated_request_rejected(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_drivers(self):
        create_driver(driver_number=1)
        create_driver(driver_number=44, full_name='Lewis HAMILTON',
                      name_acronym='HAM', team_name='Mercedes',
                      team_colour='#27F4D2')

        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_filter_active_drivers(self):
        create_driver(driver_number=1, is_active=True)
        create_driver(driver_number=99, full_name='Retired DRIVER',
                      name_acronym='RET', team_name='None',
                      team_colour='#000000', is_active=False)

        self.client.force_authenticate(self.user)
        res = self.client.get(self.url, {'active': 'true'})

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['driver_number'], 1)

    def test_drivers_ordered_by_number(self):
        create_driver(driver_number=44, full_name='Lewis HAMILTON',
                      name_acronym='HAM', team_name='Mercedes',
                      team_colour='#27F4D2')
        create_driver(driver_number=1)

        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)

        self.assertEqual(res.data[0]['driver_number'], 1)
        self.assertEqual(res.data[1]['driver_number'], 44)

    def test_empty_list_returns_200(self):
        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 0)


class DriverDetailViewTest(TestCase):
    """Tests for GET /f1/api/drivers/<driver_number>/."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user()

    def test_unauthenticated_request_rejected(self):
        driver = create_driver()
        url = reverse(
            'f1_pitwall:driver-detail',
            kwargs={'driver_number': driver.driver_number},
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_driver_detail(self):
        driver = create_driver()
        url = reverse(
            'f1_pitwall:driver-detail',
            kwargs={'driver_number': driver.driver_number},
        )

        self.client.force_authenticate(self.user)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['driver_number'], 1)
        self.assertEqual(res.data['full_name'], 'Max VERSTAPPEN')
        self.assertIn('headshot_url', res.data)
        self.assertIn('created_at', res.data)

    def test_nonexistent_driver_returns_404(self):
        url = reverse(
            'f1_pitwall:driver-detail',
            kwargs={'driver_number': 99},
        )

        self.client.force_authenticate(self.user)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


class TelemetryListViewTest(TestCase):
    """Tests for GET /f1/api/telemetry/<session_key>/."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user(email='telem@example.com')
        self.session = create_session(session_key=9158)
        self.driver1 = create_driver(driver_number=1)
        self.driver44 = create_driver(
            driver_number=44,
            full_name='Lewis HAMILTON',
            name_acronym='HAM',
            team_name='Mercedes',
            team_colour='#27F4D2',
        )
        self.url = reverse(
            'f1_pitwall:telemetry-list',
            kwargs={'session_key': self.session.session_key},
        )

    def test_unauthenticated_request_rejected(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_telemetry_for_session(self):
        create_telemetry(self.session, self.driver1, '2024-03-02T15:00:01Z')
        create_telemetry(self.session, self.driver44, '2024-03-02T15:00:02Z')

        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        self.assertEqual(res.data[0]['driver_number'], 1)
        self.assertEqual(res.data[1]['driver_number'], 44)

    def test_filter_by_driver(self):
        create_telemetry(self.session, self.driver1, '2024-03-02T15:00:01Z')
        create_telemetry(self.session, self.driver44, '2024-03-02T15:00:02Z')

        self.client.force_authenticate(self.user)
        res = self.client.get(self.url, {'driver': 44})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['driver_number'], 44)

    def test_filter_by_date_range(self):
        create_telemetry(self.session, self.driver1, '2024-03-02T15:00:01Z')
        create_telemetry(self.session, self.driver1, '2024-03-02T15:00:05Z')
        create_telemetry(self.session, self.driver1, '2024-03-02T15:00:10Z')

        self.client.force_authenticate(self.user)
        res = self.client.get(self.url, {
            'date_from': '2024-03-02T15:00:04Z',
            'date_to': '2024-03-02T15:00:09Z',
        })

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['timestamp'], '2024-03-02T15:00:05Z')

    def test_nonexistent_session_returns_404(self):
        url = reverse(
            'f1_pitwall:telemetry-list',
            kwargs={'session_key': 99999},
        )

        self.client.force_authenticate(self.user)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


class TelemetryLatestViewTest(TestCase):
    """Tests for GET /f1/api/telemetry/<session_key>/latest/."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user(email='telem_latest@example.com')
        self.session = create_session(session_key=9300)
        self.driver1 = create_driver(driver_number=1)
        self.driver44 = create_driver(
            driver_number=44,
            full_name='Lewis HAMILTON',
            name_acronym='HAM',
            team_name='Mercedes',
            team_colour='#27F4D2',
        )
        self.url = reverse(
            'f1_pitwall:telemetry-latest',
            kwargs={'session_key': self.session.session_key},
        )

    def test_unauthenticated_request_rejected(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_latest_per_driver(self):
        create_telemetry(self.session, self.driver1, '2024-03-02T15:00:01Z')
        create_telemetry(
            self.session, self.driver1, '2024-03-02T15:00:05Z', speed=305,
        )
        create_telemetry(self.session, self.driver44, '2024-03-02T15:00:02Z')
        create_telemetry(
            self.session, self.driver44, '2024-03-02T15:00:06Z', speed=306,
        )

        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        self.assertEqual(res.data[0]['driver_number'], 1)
        self.assertEqual(res.data[0]['speed'], 305)
        self.assertIn('data_source', res.data[0])
        self.assertIn('is_fallback', res.data[0])
        self.assertEqual(res.data[0]['data_source'], 'openf1_car_data')
        self.assertFalse(res.data[0]['is_fallback'])
        self.assertEqual(res.data[1]['driver_number'], 44)
        self.assertEqual(res.data[1]['speed'], 306)

    def test_empty_session_returns_empty_list(self):
        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 0)


class LapDataListViewTest(TestCase):
    """Tests for GET /f1/api/laps/<session_key>/."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user(email='laps@example.com')
        self.session = create_session(session_key=9400)
        self.driver1 = create_driver(driver_number=1)
        self.driver16 = create_driver(
            driver_number=16,
            full_name='Charles LECLERC',
            name_acronym='LEC',
            team_name='Ferrari',
            team_colour='#E8002D',
        )
        self.url = reverse(
            'f1_pitwall:lap-list',
            kwargs={'session_key': self.session.session_key},
        )

    def test_unauthenticated_request_rejected(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_lists_laps_for_session(self):
        create_lap(self.session, self.driver1, lap_number=1, lap_duration=91.1)
        create_lap(self.session, self.driver1, lap_number=2, lap_duration=90.7)
        create_lap(self.session, self.driver16, lap_number=1, lap_duration=91.5)

        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 3)
        self.assertEqual(res.data[0]['driver_number'], 1)
        self.assertEqual(res.data[0]['lap_number'], 1)
        self.assertEqual(res.data[2]['driver_number'], 16)

    def test_filters_by_driver(self):
        create_lap(self.session, self.driver1, lap_number=1)
        create_lap(self.session, self.driver16, lap_number=1)

        self.client.force_authenticate(self.user)
        res = self.client.get(self.url, {'driver': 16})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['driver_number'], 16)

    def test_nonexistent_session_returns_404(self):
        url = reverse(
            'f1_pitwall:lap-list',
            kwargs={'session_key': 99999},
        )

        self.client.force_authenticate(self.user)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_excludes_laps_from_other_sessions(self):
        other_session = create_session(session_key=9402)
        create_lap(self.session, self.driver1, lap_number=1)
        create_lap(other_session, self.driver1, lap_number=2)

        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['session_key'], self.session.session_key)


class FastestLapsViewTest(TestCase):
    """Tests for GET /f1/api/laps/<session_key>/fastest/."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user(email='fastlaps@example.com')
        self.session = create_session(session_key=9401)
        self.driver1 = create_driver(driver_number=1)
        self.driver16 = create_driver(
            driver_number=16,
            full_name='Charles LECLERC',
            name_acronym='LEC',
            team_name='Ferrari',
            team_colour='#E8002D',
        )
        self.url = reverse(
            'f1_pitwall:lap-fastest',
            kwargs={'session_key': self.session.session_key},
        )

    def test_unauthenticated_request_rejected(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_fastest_lap_per_driver(self):
        create_lap(self.session, self.driver1, lap_number=1, lap_duration=91.2)
        create_lap(self.session, self.driver1, lap_number=2, lap_duration=90.8)
        create_lap(self.session, self.driver16, lap_number=1, lap_duration=92.1)
        create_lap(self.session, self.driver16, lap_number=2, lap_duration=91.9)

        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        self.assertEqual(res.data[0]['driver_number'], 1)
        self.assertEqual(res.data[0]['lap_duration'], 90.8)
        self.assertEqual(res.data[1]['driver_number'], 16)
        self.assertEqual(res.data[1]['lap_duration'], 91.9)

    def test_ignores_incomplete_laps(self):
        create_lap(self.session, self.driver1, lap_number=1, lap_duration=None)
        create_lap(self.session, self.driver1, lap_number=2, lap_duration=91.0)

        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['lap_number'], 2)

    def test_empty_session_returns_empty_list(self):
        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 0)

    def test_uses_earlier_lap_number_when_times_tie(self):
        create_lap(self.session, self.driver1, lap_number=5, lap_duration=90.5)
        create_lap(self.session, self.driver1, lap_number=6, lap_duration=90.5)

        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['lap_number'], 5)

    def test_excludes_other_sessions_from_fastest(self):
        other_session = create_session(session_key=9403)
        create_lap(self.session, self.driver1, lap_number=1, lap_duration=91.0)
        create_lap(other_session, self.driver1, lap_number=2, lap_duration=89.0)

        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['lap_number'], 1)


class StrategyCalculateViewTest(TestCase):
    """Tests for POST /f1/api/strategy/<session_key>/calculate/."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user(email='strategy@example.com')
        self.session = create_session(session_key=9500)
        self.url = reverse(
            'f1_pitwall:strategy-calculate',
            kwargs={'session_key': self.session.session_key},
        )
        self.payload = {
            'current_lap': 20,
            'total_laps': 57,
            'current_compound': 'SOFT',
            'tyre_age': 10,
            'base_lap_time': 90.0,
            'weather_forecast': {'rain_probability': 0.3, 'rain_eta_laps': 9},
            'gap_ahead': 8.0,
            'gap_behind': 5.0,
        }

    def test_unauthenticated_request_rejected(self):
        res = self.client.post(self.url, self.payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_nonexistent_session_returns_404(self):
        url = reverse(
            'f1_pitwall:strategy-calculate',
            kwargs={'session_key': 99999},
        )
        self.client.force_authenticate(self.user)
        res = self.client.post(url, self.payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_returns_strategy_list_with_expected_fields(self):
        self.client.force_authenticate(self.user)
        res = self.client.post(self.url, self.payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['session_key'], self.session.session_key)
        self.assertIn('count', res.data)
        self.assertIn('strategies', res.data)
        self.assertTrue(len(res.data['strategies']) >= 1)

        strategy = res.data['strategies'][0]
        self.assertIn('name', strategy)
        self.assertIn('total_time', strategy)
        self.assertIn('pit_stops', strategy)
        self.assertIn('tire_risk', strategy)
        self.assertIn('weather_risk', strategy)
        self.assertIn('undercut_potential', strategy)
        self.assertIn('overcut_potential', strategy)
        self.assertIn('notes', strategy)
        self.assertIn('score', strategy)

    def test_invalid_payload_returns_400(self):
        invalid = dict(self.payload)
        invalid['current_lap'] = 58
        invalid['total_laps'] = 57

        self.client.force_authenticate(self.user)
        res = self.client.post(self.url, invalid, format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('current_lap', res.data)


class StrategyStintsViewTest(TestCase):
    """Tests for GET /f1/api/strategy/<session_key>/stints/."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user(email='strategy_stints@example.com')
        self.session = create_session(session_key=9510)
        self.other_session = create_session(session_key=9511)
        self.driver1 = create_driver(driver_number=1)
        self.driver44 = create_driver(
            driver_number=44,
            full_name='Lewis HAMILTON',
            name_acronym='HAM',
            team_name='Mercedes',
            team_colour='#27F4D2',
        )
        create_stint(
            self.session, self.driver44, stint_number=2,
            compound='MEDIUM', lap_start=21, lap_end=35, tyre_age_at_start=0,
        )
        create_stint(
            self.session, self.driver1, stint_number=1,
            compound='SOFT', lap_start=1, lap_end=20, tyre_age_at_start=0,
        )
        create_stint(
            self.other_session, self.driver1, stint_number=1,
            compound='HARD', lap_start=1, lap_end=18, tyre_age_at_start=2,
        )
        self.url = reverse(
            'f1_pitwall:strategy-stints',
            kwargs={'session_key': self.session.session_key},
        )

    def test_unauthenticated_request_rejected(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_nonexistent_session_returns_404(self):
        url = reverse(
            'f1_pitwall:strategy-stints',
            kwargs={'session_key': 99999},
        )
        self.client.force_authenticate(self.user)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_returns_stints_for_session_only(self):
        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        session_keys = {row['session_key'] for row in res.data}
        self.assertEqual(session_keys, {self.session.session_key})

    def test_returns_ordered_by_driver_then_stint_number(self):
        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0]['driver_number'], 1)
        self.assertEqual(res.data[0]['stint_number'], 1)
        self.assertEqual(res.data[1]['driver_number'], 44)
        self.assertEqual(res.data[1]['stint_number'], 2)

    def test_payload_contains_expected_stint_fields(self):
        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        row = res.data[0]
        self.assertIn('session_key', row)
        self.assertIn('driver_number', row)
        self.assertIn('stint_number', row)
        self.assertIn('compound', row)
        self.assertIn('tyre_age_at_start', row)
        self.assertIn('lap_start', row)
        self.assertIn('lap_end', row)


class WeatherTimelineViewTest(TestCase):
    """Tests for GET /f1/api/weather/<session_key>/."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user(email='weather_timeline@example.com')
        self.session = create_session(session_key=9600)
        create_weather(self.session, '2024-03-02T15:00:00Z', humidity=55.0)
        create_weather(self.session, '2024-03-02T15:05:00Z', humidity=62.0)
        self.url = reverse(
            'f1_pitwall:weather-timeline',
            kwargs={'session_key': self.session.session_key},
        )

    @patch('f1_pitwall.views.weather.WeatherService.get_weather_history')
    def test_unauthenticated_request_rejected(self, mock_history):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        mock_history.assert_not_called()

    @patch('f1_pitwall.views.weather.WeatherService.get_weather_history')
    def test_returns_weather_timeline(self, mock_history):
        mock_history.return_value = WeatherData.objects.filter(session=self.session)
        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        self.assertEqual(res.data[0]['session_key'], self.session.session_key)
        self.assertIn('humidity', res.data[0])

    @patch('f1_pitwall.views.weather.WeatherService.get_weather_history')
    def test_nonexistent_session_returns_404(self, mock_history):
        url = reverse(
            'f1_pitwall:weather-timeline',
            kwargs={'session_key': 99999},
        )
        self.client.force_authenticate(self.user)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        mock_history.assert_not_called()


class WeatherCurrentViewTest(TestCase):
    """Tests for GET /f1/api/weather/<session_key>/current/."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user(email='weather_current@example.com')
        self.session = create_session(session_key=9601)
        self.current = create_weather(
            self.session,
            '2024-03-02T15:10:00Z',
            humidity=70.0,
        )
        self.url = reverse(
            'f1_pitwall:weather-current',
            kwargs={'session_key': self.session.session_key},
        )

    @patch('f1_pitwall.views.weather.WeatherService.get_current_weather')
    def test_returns_current_weather(self, mock_current):
        mock_current.return_value = self.current
        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['session_key'], self.session.session_key)
        self.assertEqual(res.data['humidity'], 70.0)

    @patch('f1_pitwall.views.weather.WeatherService.get_current_weather')
    def test_returns_detail_when_no_current_weather(self, mock_current):
        mock_current.return_value = None
        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('detail', res.data)


class WeatherForecastViewTest(TestCase):
    """Tests for GET /f1/api/weather/<session_key>/forecast/."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user(email='weather_forecast@example.com')
        self.session = create_session(session_key=9602)
        self.url = reverse(
            'f1_pitwall:weather-forecast',
            kwargs={'session_key': self.session.session_key},
        )

    @patch('f1_pitwall.views.weather.WeatherService.calculate_rain_forecast')
    def test_returns_forecast_payload(self, mock_forecast):
        mock_forecast.return_value = {
            'rain_probability': 0.65,
            'rain_eta_laps': 6,
            'heavy_rain': False,
            'rain_intensity': 0.58,
        }
        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['rain_probability'], 0.65)
        self.assertEqual(res.data['rain_eta_laps'], 6)
        self.assertEqual(res.data['heavy_rain'], False)
        self.assertEqual(res.data['rain_intensity'], 0.58)

    @patch('f1_pitwall.views.weather.WeatherService.calculate_rain_forecast')
    def test_nonexistent_session_returns_404(self, mock_forecast):
        url = reverse(
            'f1_pitwall:weather-forecast',
            kwargs={'session_key': 99999},
        )
        self.client.force_authenticate(self.user)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        mock_forecast.assert_not_called()


class RaceControlListViewTest(TestCase):
    """Tests for GET /f1/api/race-control/<session_key>/."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user(email='rc_list@example.com')
        self.session = create_session(session_key=9700)
        self.url = reverse(
            'f1_pitwall:race-control-list',
            kwargs={'session_key': self.session.session_key},
        )

    def test_unauthenticated_request_rejected(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('f1_pitwall.views.race_control.RaceControlService.get_messages')
    def test_returns_message_list(self, mock_get_messages):
        create_race_control(
            self.session, '2024-03-02T15:00:00Z',
            flag='YELLOW', message='Yellow flag in sector 2',
        )
        mock_get_messages.return_value = RaceControlMessage.objects.filter(
            session=self.session,
        )
        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['session_key'], self.session.session_key)
        self.assertEqual(res.data[0]['flag'], 'YELLOW')

    @patch('f1_pitwall.views.race_control.RaceControlService.get_messages')
    def test_nonexistent_session_returns_404(self, mock_get_messages):
        url = reverse(
            'f1_pitwall:race-control-list',
            kwargs={'session_key': 99999},
        )
        self.client.force_authenticate(self.user)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        mock_get_messages.assert_not_called()


class RaceControlFlagsViewTest(TestCase):
    """Tests for GET /f1/api/race-control/<session_key>/flags/."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user(email='rc_flags@example.com')
        self.session = create_session(session_key=9701)
        self.url = reverse(
            'f1_pitwall:race-control-flags',
            kwargs={'session_key': self.session.session_key},
        )

    def test_unauthenticated_request_rejected(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('f1_pitwall.views.race_control.RaceControlService.is_safety_car_active')
    @patch('f1_pitwall.views.race_control.RaceControlService.get_latest_flag')
    def test_returns_latest_flag_payload(self, mock_get_latest_flag, mock_sc):
        mock_get_latest_flag.return_value = 'YELLOW'
        mock_sc.return_value = True
        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['session_key'], self.session.session_key)
        self.assertEqual(res.data['latest_flag'], 'YELLOW')
        self.assertTrue(res.data['safety_car_active'])

    @patch('f1_pitwall.views.race_control.RaceControlService.get_latest_flag')
    def test_nonexistent_session_returns_404(self, mock_get_latest_flag):
        url = reverse(
            'f1_pitwall:race-control-flags',
            kwargs={'session_key': 99999},
        )
        self.client.force_authenticate(self.user)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        mock_get_latest_flag.assert_not_called()
