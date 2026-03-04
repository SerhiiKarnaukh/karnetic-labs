"""Tests for WeatherService history sync and rain forecasting."""

from unittest.mock import AsyncMock, MagicMock

from django.test import TestCase

from f1_pitwall.models import Session, WeatherData
from f1_pitwall.services.weather_service import WeatherService


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


def make_weather_rows():
    return [
        {
            'date': '2024-03-02T15:00:00+00:00',
            'air_temperature': 29.0,
            'track_temperature': 36.0,
            'humidity': 55.0,
            'wind_speed': 2.5,
            'wind_direction': 100,
            'rainfall': 0,
            'pressure': 1014.0,
        },
        {
            'date': '2024-03-02T15:05:00+00:00',
            'air_temperature': 28.0,
            'track_temperature': 34.0,
            'humidity': 72.0,
            'wind_speed': 4.0,
            'wind_direction': 120,
            'rainfall': 0,
            'pressure': 1011.0,
        },
        {
            'date': '2024-03-02T15:10:00+00:00',
            'air_temperature': 27.5,
            'track_temperature': 32.0,
            'humidity': 86.0,
            'wind_speed': 5.8,
            'wind_direction': 140,
            'rainfall': 0,
            'pressure': 1008.5,
        },
    ]


class WeatherServiceHistoryTest(TestCase):
    """Data synchronization and current weather retrieval."""

    def setUp(self):
        self.session = create_session()
        self.client = MagicMock()
        self.client.get_weather = AsyncMock(return_value=make_weather_rows())
        self.service = WeatherService(client=self.client)

    def test_get_weather_history_persists_rows(self):
        queryset = self.service.get_weather_history(self.session.session_key)
        self.assertEqual(queryset.count(), 3)
        self.assertEqual(WeatherData.objects.count(), 3)

    def test_get_weather_history_is_idempotent(self):
        self.service.get_weather_history(self.session.session_key)
        self.service.get_weather_history(self.session.session_key)
        self.assertEqual(WeatherData.objects.count(), 3)

    def test_get_current_weather_returns_latest_timestamp(self):
        latest = self.service.get_current_weather(self.session.session_key)
        self.assertIsNotNone(latest)
        self.assertEqual(latest.humidity, 86.0)

    def test_get_weather_history_unknown_session_returns_empty(self):
        queryset = self.service.get_weather_history(999999)
        self.assertEqual(queryset.count(), 0)
        self.client.get_weather.assert_not_awaited()

    def test_sync_handles_invalid_rows_without_crash(self):
        self.client.get_weather = AsyncMock(return_value=[
            {'date': 'invalid-date', 'humidity': 80},
            {'date': '2024-03-02T15:00:00+00:00', 'humidity': 'bad'},
        ])
        service = WeatherService(client=self.client)
        queryset = service.get_weather_history(self.session.session_key)
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().humidity, 0.0)


class WeatherServiceForecastTest(TestCase):
    """Rain probability, ETA, and likely-rain decisions."""

    def setUp(self):
        self.session = create_session()
        self.client = MagicMock()
        self.client.get_weather = AsyncMock(return_value=make_weather_rows())
        self.service = WeatherService(client=self.client)

    def test_calculate_rain_forecast_returns_expected_shape(self):
        forecast = self.service.calculate_rain_forecast(self.session.session_key)
        self.assertIn('rain_probability', forecast)
        self.assertIn('rain_eta_laps', forecast)
        self.assertIn('heavy_rain', forecast)
        self.assertIn('rain_intensity', forecast)

    def test_forecast_accuracy_matrix(self):
        """Parameterized weather forecast accuracy checks."""
        strong_signal = make_weather_rows()
        active_rain = make_weather_rows()
        active_rain[-1]['rainfall'] = 1
        active_rain[-1]['humidity'] = 93.0
        low_signal = [
            {
                'date': '2024-03-02T15:00:00+00:00',
                'air_temperature': 30.0,
                'track_temperature': 40.0,
                'humidity': 40.0,
                'wind_speed': 2.0,
                'wind_direction': 100,
                'rainfall': 0,
                'pressure': 1013.0,
            },
            {
                'date': '2024-03-02T15:05:00+00:00',
                'air_temperature': 30.0,
                'track_temperature': 39.5,
                'humidity': 42.0,
                'wind_speed': 2.0,
                'wind_direction': 110,
                'rainfall': 0,
                'pressure': 1012.9,
            },
        ]
        cases = [
            ('strong_signal', strong_signal, 0.5, 1.0, True, True),
            ('active_rain', active_rain, 1.0, 1.0, True, True),
            ('low_signal', low_signal, 0.0, 0.49, False, False),
        ]
        for label, rows, min_prob, max_prob, expect_heavy, expect_eta in cases:
            with self.subTest(label=label):
                WeatherData.objects.filter(session=self.session).delete()
                self.client.get_weather = AsyncMock(return_value=rows)
                service = WeatherService(client=self.client)
                forecast = service.calculate_rain_forecast(self.session.session_key)
                self.assertGreaterEqual(forecast['rain_probability'], min_prob)
                self.assertLessEqual(forecast['rain_probability'], max_prob)
                self.assertEqual(forecast['heavy_rain'], expect_heavy)
                if expect_eta:
                    self.assertIsNotNone(forecast['rain_eta_laps'])
                else:
                    self.assertIsNone(forecast['rain_eta_laps'])

    def test_forecast_probability_increases_with_rising_humidity_and_drop_pressure(self):
        forecast = self.service.calculate_rain_forecast(self.session.session_key)
        self.assertGreaterEqual(forecast['rain_probability'], 0.5)
        self.assertIsNotNone(forecast['rain_eta_laps'])

    def test_active_rain_sets_immediate_eta(self):
        rainy_rows = make_weather_rows()
        rainy_rows[-1]['rainfall'] = 1
        rainy_rows[-1]['humidity'] = 93.0
        self.client.get_weather = AsyncMock(return_value=rainy_rows)
        service = WeatherService(client=self.client)

        forecast = service.calculate_rain_forecast(self.session.session_key)
        self.assertEqual(forecast['rain_probability'], 1.0)
        self.assertEqual(forecast['rain_eta_laps'], 0)
        self.assertTrue(forecast['heavy_rain'])

    def test_low_signal_forecast_returns_low_probability(self):
        low_rows = [
            {
                'date': '2024-03-02T15:00:00+00:00',
                'air_temperature': 30,
                'track_temperature': 40,
                'humidity': 40,
                'wind_speed': 2,
                'wind_direction': 100,
                'rainfall': 0,
                'pressure': 1013,
            },
            {
                'date': '2024-03-02T15:05:00+00:00',
                'air_temperature': 30,
                'track_temperature': 40,
                'humidity': 42,
                'wind_speed': 2,
                'wind_direction': 110,
                'rainfall': 0,
                'pressure': 1012.9,
            },
        ]
        self.client.get_weather = AsyncMock(return_value=low_rows)
        service = WeatherService(client=self.client)

        forecast = service.calculate_rain_forecast(self.session.session_key)
        self.assertLess(forecast['rain_probability'], 0.5)

    def test_is_rain_likely_true_within_horizon(self):
        self.assertTrue(
            self.service.is_rain_likely(self.session.session_key, within_laps=10),
        )

    def test_is_rain_likely_false_when_horizon_too_short(self):
        self.assertFalse(
            self.service.is_rain_likely(self.session.session_key, within_laps=1),
        )

    def test_is_rain_likely_horizon_matrix(self):
        cases = [
            (1, False),
            (3, False),
            (5, True),
            (10, True),
            (12, True),
        ]
        for horizon, expected in cases:
            with self.subTest(horizon=horizon):
                result = self.service.is_rain_likely(
                    self.session.session_key, within_laps=horizon,
                )
                self.assertEqual(result, expected)

    def test_forecast_defaults_when_no_data(self):
        self.client.get_weather = AsyncMock(return_value=[])
        service = WeatherService(client=self.client)
        forecast = service.calculate_rain_forecast(self.session.session_key)
        self.assertEqual(forecast['rain_probability'], 0.0)
        self.assertIsNone(forecast['rain_eta_laps'])
        self.assertFalse(forecast['heavy_rain'])
        self.assertEqual(forecast['rain_intensity'], 0.0)
