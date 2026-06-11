import uuid

from django.db import models
from django.utils.timesince import timesince

from social_profiles.models import Profile


class Like(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(
        Profile,
        related_name='likes',
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)


class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    body = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        Profile,
        related_name='comments',
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created_at', )

    def created_at_formatted(self):
        return timesince(self.created_at)
