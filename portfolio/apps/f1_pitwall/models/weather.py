"""WeatherData model - track weather conditions during a session."""

import uuid

from django.db import models


class WeatherData(models.Model):
    """Track weather conditions recorded at intervals during a session."""

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
    )
    session = models.ForeignKey(
        'f1_pitwall.Session',
        on_delete=models.CASCADE,
        related_name='weather',
    )
    timestamp = models.DateTimeField()
    air_temperature = models.FloatField(help_text="Degrees Celsius")
    track_temperature = models.FloatField(help_text="Degrees Celsius")
    humidity = models.FloatField(help_text="Percentage, 0-100")
    wind_speed = models.FloatField(help_text="Meters per second")
    wind_direction = models.IntegerField(help_text="Degrees, 0-360")
    rainfall = models.BooleanField(default=False)
    pressure = models.FloatField(
        null=True, blank=True,
        help_text="Atmospheric pressure in millibars",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        rain = " (RAIN)" if self.rainfall else ""
        return (
            f"Weather {self.session_id} @ {self.timestamp} "
            f"- {self.air_temperature}°C{rain}"
        )
