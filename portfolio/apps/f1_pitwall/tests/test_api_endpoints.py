"""Tests for basic REST API endpoints: sessions and drivers."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from f1_pitwall.models import Driver, Session

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
        url = reverse('f1_pitwall:session-detail',
                       kwargs={'session_key': session.session_key})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_session_detail(self):
        session = create_session()
        url = reverse('f1_pitwall:session-detail',
                       kwargs={'session_key': session.session_key})

        self.client.force_authenticate(self.user)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['session_key'], session.session_key)
        self.assertEqual(res.data['circuit_name'],
                         'Bahrain International Circuit')
        self.assertIn('meeting_key', res.data)
        self.assertIn('created_at', res.data)

    def test_nonexistent_session_returns_404(self):
        url = reverse('f1_pitwall:session-detail',
                       kwargs={'session_key': 99999})

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
        url = reverse('f1_pitwall:driver-detail',
                       kwargs={'driver_number': driver.driver_number})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_driver_detail(self):
        driver = create_driver()
        url = reverse('f1_pitwall:driver-detail',
                       kwargs={'driver_number': driver.driver_number})

        self.client.force_authenticate(self.user)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['driver_number'], 1)
        self.assertEqual(res.data['full_name'], 'Max VERSTAPPEN')
        self.assertIn('headshot_url', res.data)
        self.assertIn('created_at', res.data)

    def test_nonexistent_driver_returns_404(self):
        url = reverse('f1_pitwall:driver-detail',
                       kwargs={'driver_number': 99})

        self.client.force_authenticate(self.user)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
