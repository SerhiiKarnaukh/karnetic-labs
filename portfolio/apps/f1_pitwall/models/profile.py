"""F1 user profile model with role-based access level."""

from django.db import models

from accounts.models import Account


class F1UserProfile(models.Model):
    """One-to-one profile for F1 module users."""

    class Role(models.TextChoices):
        VIEWER = 'viewer', 'Viewer'
        ENGINEER = 'engineer', 'Engineer'
        ADMIN = 'admin', 'Admin'

    user = models.OneToOneField(
        Account,
        on_delete=models.CASCADE,
        related_name='f1_profile',
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER,
    )

    def __str__(self):
        return f"{self.user.email} ({self.role})"
