import uuid

from django.db import models
from django.utils.timesince import timesince

from social_profiles.models import Profile
from social_chat.models.conversation import Conversation


class ConversationMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        related_name='messages',
        on_delete=models.CASCADE,
    )
    body = models.TextField()
    sent_to = models.ForeignKey(
        Profile,
        related_name='received_messages',
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        Profile,
        related_name='sent_messages',
        on_delete=models.CASCADE,
    )

    def created_at_formatted(self):
        return timesince(self.created_at)
