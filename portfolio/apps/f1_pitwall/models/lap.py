"""LapData model - timing data for a single lap by a single driver."""

import uuid

from django.db import models


class LapData(models.Model):
    """Timing data for one lap: sector times, speed trap, pit flags."""

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
    )
    session = models.ForeignKey(
        'f1_pitwall.Session',
        on_delete=models.CASCADE,
        related_name='laps',
    )
    driver = models.ForeignKey(
        'f1_pitwall.Driver',
        on_delete=models.CASCADE,
        related_name='laps',
    )
    lap_number = models.IntegerField()
    lap_duration = models.FloatField(
        null=True, blank=True,
        help_text="Total lap time in seconds, null for incomplete laps",
    )
    sector_1 = models.FloatField(
        null=True, blank=True, help_text="Sector 1 time in seconds",
    )
    sector_2 = models.FloatField(
        null=True, blank=True, help_text="Sector 2 time in seconds",
    )
    sector_3 = models.FloatField(
        null=True, blank=True, help_text="Sector 3 time in seconds",
    )
    speed_trap = models.FloatField(
        null=True, blank=True, help_text="Speed at the speed trap in km/h",
    )
    is_pit_out_lap = models.BooleanField(default=False)
    is_pit_in_lap = models.BooleanField(default=False)
    is_personal_best = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['lap_number']
        constraints = [
            models.UniqueConstraint(
                fields=['session', 'driver', 'lap_number'],
                name='uq_lap_session_driver_number',
            ),
        ]

    def __str__(self):
        time_str = f"{self.lap_duration:.3f}s" if self.lap_duration else "N/A"
        return f"Lap {self.lap_number} - {self.driver_id} - {time_str}"
