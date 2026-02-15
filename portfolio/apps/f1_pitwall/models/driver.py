"""F1 Driver model - stores driver information and team affiliations."""

import uuid

from django.db import models


class Driver(models.Model):
    """An F1 driver with team affiliation and visual identifiers."""

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
    )
    driver_number = models.IntegerField(
        unique=True,
        help_text="Car number, e.g. 1 for Verstappen, 44 for Hamilton",
    )
    full_name = models.CharField(max_length=100)
    name_acronym = models.CharField(
        max_length=3, help_text='e.g. "VER", "HAM", "NOR"',
    )
    team_name = models.CharField(max_length=100)
    team_colour = models.CharField(
        max_length=7, help_text='Hex color, e.g. "#3671C6"',
    )
    headshot_url = models.URLField(blank=True)
    country_code = models.CharField(max_length=3, blank=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Currently competing in the championship",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['driver_number']

    def __str__(self):
        return f"#{self.driver_number} {self.name_acronym} ({self.team_name})"
