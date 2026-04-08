"""Weather data fetching, caching, and rain probability forecasting."""

import logging

from asgiref.sync import async_to_sync
from django.utils.dateparse import parse_datetime

from f1_pitwall.exceptions import F1PitwallError
from f1_pitwall.models import Session, WeatherData
from f1_pitwall.services.openf1_client import OpenF1Client

logger = logging.getLogger(__name__)

RECENT_FORECAST_POINTS = 10


class WeatherService:
    """Fetch weather data and derive rain probability/ETA forecast."""

    def __init__(self, client=None):
        self.client = client or OpenF1Client()

    def get_current_weather(self, session_key):
        """Return latest weather row after synchronizing with OpenF1."""
        self.get_weather_history(session_key)
        return WeatherData.objects.filter(
            session__session_key=session_key,
        ).order_by('-timestamp').first()

    def get_weather_history(self, session_key):
        """Fetch weather timeline, upsert to DB, and return queryset."""
        session = self._session(session_key)
        if session is None:
            return WeatherData.objects.none()

        for raw in self._fetch_weather(session_key):
            self._upsert_weather_row(session, raw)
        return WeatherData.objects.filter(session=session)

    def calculate_rain_forecast(self, session_key):
        """Return probability + ETA in laps from recent weather trends."""
        history = self._recent_weather(session_key)
        if not history:
            return self._default_forecast()

        latest = history[-1]
        if latest.rainfall:
            return self._active_rain_forecast(latest)

        probability = self._rain_probability_from_trends(history)
        eta_laps = self._rain_eta_laps(probability, history)
        intensity = self._rain_intensity(probability, history, latest)
        return {
            'rain_probability': round(probability, 3),
            'rain_eta_laps': eta_laps,
            'heavy_rain': intensity >= 0.7,
            'rain_intensity': round(intensity, 3),
        }

    def is_rain_likely(self, session_key, within_laps=10):
        """Check if forecasted rain is likely within the requested horizon."""
        forecast = self.calculate_rain_forecast(session_key)
        eta = forecast.get('rain_eta_laps')
        if forecast['rain_probability'] < 0.5:
            return False
        if eta is None:
            return False
        return eta <= within_laps

    def _fetch_weather(self, session_key):
        async def _fetch():
            return await self.client.get_weather(session_key)

        try:
            return async_to_sync(_fetch)()
        except F1PitwallError as exc:
            logger.warning(
                'Weather fetch skipped for session %s: %s', session_key, exc,
            )
            return []

    def _session(self, session_key):
        return Session.objects.filter(session_key=session_key).first()

    def _upsert_weather_row(self, session, raw):
        timestamp = parse_datetime(raw.get('date') or '')
        if timestamp is None:
            return

        defaults = {
            'air_temperature': self._to_float(raw.get('air_temperature'), 0.0),
            'track_temperature': self._to_float(raw.get('track_temperature'), 0.0),
            'humidity': self._to_float(raw.get('humidity'), 0.0),
            'wind_speed': self._to_float(raw.get('wind_speed'), 0.0),
            'wind_direction': self._to_int(raw.get('wind_direction'), 0),
            'rainfall': self._to_bool(raw.get('rainfall')),
            'pressure': self._to_nullable_float(raw.get('pressure')),
        }
        queryset = WeatherData.objects.filter(session=session, timestamp=timestamp)
        first = queryset.first()
        if first is None:
            WeatherData.objects.create(
                session=session,
                timestamp=timestamp,
                **defaults,
            )
            return

        queryset.exclude(pk=first.pk).delete()
        for field, value in defaults.items():
            setattr(first, field, value)
        first.save(update_fields=list(defaults.keys()))

    def _recent_weather(self, session_key):
        self.get_weather_history(session_key)
        return list(
            WeatherData.objects.filter(
                session__session_key=session_key,
            ).order_by('timestamp')[:RECENT_FORECAST_POINTS]
        )

    def _rain_probability_from_trends(self, history):
        latest = history[-1]
        earliest = history[0]

        humidity_rise = max(0.0, latest.humidity - earliest.humidity)
        pressure_drop = 0.0
        if latest.pressure is not None and earliest.pressure is not None:
            pressure_drop = max(0.0, earliest.pressure - latest.pressure)
        wind_rise = max(0.0, latest.wind_speed - earliest.wind_speed)

        probability = 0.1
        probability += min(0.35, humidity_rise / 100.0)
        probability += min(0.3, pressure_drop / 10.0)
        probability += min(0.15, wind_rise / 20.0)
        probability += self._rainfall_signal(history)
        if latest.humidity >= 85:
            probability += 0.1
        return min(1.0, max(0.0, probability))

    def _rainfall_signal(self, history):
        rainy = sum(1 for row in history if row.rainfall)
        if rainy == 0:
            return 0.0
        return min(0.3, 0.1 + (rainy / len(history)) * 0.2)

    def _rain_eta_laps(self, probability, history):
        if probability < 0.25:
            return None
        latest = history[-1]
        earliest = history[0]
        signal = 0.0
        signal += max(0.0, latest.humidity - earliest.humidity) / 40.0
        if latest.pressure is not None and earliest.pressure is not None:
            signal += max(0.0, earliest.pressure - latest.pressure) / 4.0
        signal += max(0.0, latest.wind_speed - earliest.wind_speed) / 8.0
        eta = int(round(12 - min(10.0, signal * 3)))
        return max(1, min(15, eta))

    def _rain_intensity(self, probability, history, latest):
        intensity = probability
        if latest.humidity >= 90:
            intensity += 0.1
        if latest.rainfall:
            intensity += 0.2
        rainy_recent = sum(1 for row in history[-3:] if row.rainfall)
        intensity += 0.1 * rainy_recent
        return min(1.0, intensity)

    def _default_forecast(self):
        return {
            'rain_probability': 0.0,
            'rain_eta_laps': None,
            'heavy_rain': False,
            'rain_intensity': 0.0,
        }

    def _active_rain_forecast(self, latest):
        heavy = latest.humidity >= 90 or latest.track_temperature <= 20
        return {
            'rain_probability': 1.0,
            'rain_eta_laps': 0,
            'heavy_rain': heavy,
            'rain_intensity': 0.9 if heavy else 0.7,
        }

    def _to_float(self, value, default):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _to_nullable_float(self, value):
        if value in (None, ''):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _to_int(self, value, default):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default

    def _to_bool(self, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value > 0
        if isinstance(value, str):
            return value.strip().lower() in {'1', 'true', 'yes', 'y'}
        return False
