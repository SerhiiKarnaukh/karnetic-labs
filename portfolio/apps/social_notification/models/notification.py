import uuid

from django.db import models

from social_posts.models import Post
from social_profiles.models import Profile


class Notification(models.Model):
    NEWFRIENDREQUEST = 'new_friendrequest'
    ACCEPTEDFRIENDREQUEST = 'accepted_friendrequest'
    REJECTEDFRIENDREQUEST = 'rejected_friendrequest'
    POST_LIKE = 'post_like'
    POST_COMMENT = 'post_comment'
    CHAT_MESSAGE = 'chat_message'

    CHOICES_TYPE_OF_NOTIFICATION = (
        (NEWFRIENDREQUEST, 'New friendrequest'),
        (ACCEPTEDFRIENDREQUEST, 'Accepted friendrequest'),
        (REJECTEDFRIENDREQUEST, 'Rejected friendrequest'),
        (POST_LIKE, 'Post like'),
        (POST_COMMENT, 'Post comment'),
        (CHAT_MESSAGE, 'Chat message'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    type_of_notification = models.CharField(
        max_length=50,
        choices=CHOICES_TYPE_OF_NOTIFICATION,
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    created_by = models.ForeignKey(
        Profile,
        related_name='created_notifications',
        on_delete=models.CASCADE,
    )
    created_for = models.ForeignKey(
        Profile,
        related_name='received_notifications',
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
