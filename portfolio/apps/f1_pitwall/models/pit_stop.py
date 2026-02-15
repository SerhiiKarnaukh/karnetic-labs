"""PitStop model - records each pit lane entry event."""

import uuid

from django.db import models


class PitStop(models.Model):
    """A single pit stop event for a driver during a session."""

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
    )
    session = models.ForeignKey(
        'f1_pitwall.Session',
        on_delete=models.CASCADE,
        related_name='pit_stops',
    )
    driver = models.ForeignKey(
        'f1_pitwall.Driver',
        on_delete=models.CASCADE,
        related_name='pit_stops',
    )
    lap_number = models.IntegerField(
        help_text="The lap on which the pit stop occurred",
    )
    pit_duration = models.FloatField(
        help_text="Time stationary in pit box, seconds",
    )
    timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return (
            f"Pit stop {self.driver_id} lap {self.lap_number} "
            f"- {self.pit_duration:.1f}s"
        )
