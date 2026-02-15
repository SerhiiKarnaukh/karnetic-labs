"""F1 Session model - stores racing session metadata from OpenF1 API."""

import uuid

from django.db import models

from f1_pitwall.constants import SESSION_TYPE_CHOICES


class Session(models.Model):
    """A single F1 racing session (Practice, Qualifying, Sprint, Race)."""

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
    )
    session_key = models.IntegerField(
        unique=True, db_index=True,
        help_text="OpenF1 session identifier",
    )
    meeting_key = models.IntegerField(
        db_index=True,
        help_text="OpenF1 Grand Prix identifier",
    )
    session_name = models.CharField(
        max_length=50,
        help_text='e.g. "Race", "Qualifying", "Practice 1"',
    )
    session_type = models.CharField(
        max_length=10, choices=SESSION_TYPE_CHOICES,
    )
    circuit_name = models.CharField(max_length=100)
    circuit_short_name = models.CharField(max_length=20)
    country_name = models.CharField(max_length=100)
    country_code = models.CharField(
        max_length=3, help_text="ISO 3166-1 alpha-3",
    )
    date_start = models.DateTimeField(db_index=True)
    date_end = models.DateTimeField(null=True, blank=True)
    year = models.IntegerField(db_index=True)
    is_live = models.BooleanField(
        default=False, help_text="Session currently in progress",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_start']

    def __str__(self):
        return f"{self.year} {self.circuit_short_name} - {self.session_name}"
