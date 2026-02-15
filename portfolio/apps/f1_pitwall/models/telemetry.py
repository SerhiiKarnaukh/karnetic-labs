"""TelemetrySnapshot model - high-frequency car telemetry data."""

import uuid

from django.db import models


class TelemetrySnapshot(models.Model):
    """A single telemetry reading from a car at ~3.7 Hz."""

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
    )
    session = models.ForeignKey(
        'f1_pitwall.Session',
        on_delete=models.CASCADE,
        related_name='telemetry',
    )
    driver = models.ForeignKey(
        'f1_pitwall.Driver',
        on_delete=models.CASCADE,
        related_name='telemetry',
    )
    timestamp = models.DateTimeField(db_index=True)
    speed = models.IntegerField(help_text="km/h, range 0-370")
    rpm = models.IntegerField(help_text="Engine RPM, range 0-15000")
    throttle = models.IntegerField(help_text="0-100 percentage")
    brake = models.IntegerField(help_text="0-100 percentage")
    gear = models.IntegerField(help_text="0 for neutral, 1-8")
    drs = models.IntegerField(help_text="DRS status code from OpenF1")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(
                fields=['session', 'driver', 'timestamp'],
                name='idx_telem_sess_drv_ts',
            ),
        ]

    def __str__(self):
        return (
            f"Telemetry {self.driver_id} @ {self.timestamp} "
            f"- {self.speed} km/h"
        )
