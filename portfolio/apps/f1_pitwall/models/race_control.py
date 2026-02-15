"""RaceControlMessage model - official FIA race director messages."""

import uuid

from django.db import models

from f1_pitwall.constants import FLAG_CHOICES


class RaceControlMessage(models.Model):
    """An official message from the FIA race director during a session."""

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
    )
    session = models.ForeignKey(
        'f1_pitwall.Session',
        on_delete=models.CASCADE,
        related_name='rc_messages',
    )
    timestamp = models.DateTimeField()
    category = models.CharField(
        max_length=50,
        help_text='e.g. "Flag", "SafetyCar", "Penalty"',
    )
    message = models.TextField(help_text="Full message text")
    flag = models.CharField(
        max_length=20, choices=FLAG_CHOICES, blank=True,
    )
    driver_number = models.IntegerField(
        null=True, blank=True,
        help_text="The driver the message concerns, if any",
    )
    lap_number = models.IntegerField(null=True, blank=True)
    sector = models.IntegerField(
        null=True, blank=True, help_text="1, 2, or 3",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        flag_str = f" [{self.flag}]" if self.flag else ""
        return f"RC{flag_str}: {self.message[:80]}"
