"""Stint model - a continuous run on one set of tires between pit stops."""

import uuid

from django.db import models

from f1_pitwall.constants import COMPOUND_CHOICES


class Stint(models.Model):
    """A continuous run on one set of tires between pit stops."""

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
    )
    session = models.ForeignKey(
        'f1_pitwall.Session',
        on_delete=models.CASCADE,
        related_name='stints',
    )
    driver = models.ForeignKey(
        'f1_pitwall.Driver',
        on_delete=models.CASCADE,
        related_name='stints',
    )
    stint_number = models.IntegerField(
        help_text="1 for first stint, 2 after first pit, etc.",
    )
    compound = models.CharField(max_length=15, choices=COMPOUND_CHOICES)
    tyre_age_at_start = models.IntegerField(
        default=0,
        help_text="Non-zero if starting on used tires",
    )
    lap_start = models.IntegerField()
    lap_end = models.IntegerField(
        null=True, blank=True,
        help_text="Null if stint is in progress",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['stint_number']

    def __str__(self):
        return (
            f"Stint {self.stint_number} {self.driver_id} "
            f"- {self.compound} (L{self.lap_start}-{self.lap_end or '?'})"
        )
