"""Serializers for weather timeline/current/forecast endpoints."""

from rest_framework import serializers

from f1_pitwall.models import WeatherData


class WeatherDataSerializer(serializers.ModelSerializer):
    """Serialize weather samples for API responses."""

    session_key = serializers.IntegerField(source='session.session_key')

    class Meta:
        model = WeatherData
        fields = (
            'id',
            'session_key',
            'timestamp',
            'air_temperature',
            'track_temperature',
            'humidity',
            'wind_speed',
            'wind_direction',
            'rainfall',
            'pressure',
        )


class WeatherForecastSerializer(serializers.Serializer):
    """Serialize forecast payload returned by WeatherService."""

    rain_probability = serializers.FloatField()
    rain_eta_laps = serializers.IntegerField(allow_null=True)
    heavy_rain = serializers.BooleanField()
    rain_intensity = serializers.FloatField()
