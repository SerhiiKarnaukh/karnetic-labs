from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from core.utils import create_active_user
from social_profiles.models import FriendshipRequest, Profile
from social_profiles.tasks.profile import (
    create_social_friend_suggestions,
    delete_old_rejected_friendship_requests,
)


class SocialProfileTaskTests(TestCase):
    def create_profile(self, username):
        user = create_active_user(
            email=f'{username}@example.com',
            username=username,
            password='testpass123',
            first_name=username,
            last_name='User',
        )
        return Profile.objects.create(user=user)

    def test_creates_friend_of_friend_suggestion(self):
        user = self.create_profile('user')
        friend = self.create_profile('friend')
        suggestion = self.create_profile('suggestion')
        user.friends.add(friend)
        friend.friends.add(suggestion)

        create_social_friend_suggestions()

        self.assertTrue(user.people_you_may_know.filter(pk=suggestion.pk).exists())
        self.assertFalse(user.people_you_may_know.filter(pk=user.pk).exists())

    def test_deletes_only_old_rejected_requests(self):
        sender = self.create_profile('sender')
        recipient = self.create_profile('recipient')
        old = FriendshipRequest.objects.create(
            created_by=sender,
            created_for=recipient,
            status=FriendshipRequest.REJECTED,
        )
        recent = FriendshipRequest.objects.create(
            created_by=recipient,
            created_for=sender,
            status=FriendshipRequest.REJECTED,
        )
        FriendshipRequest.objects.filter(pk=old.pk).update(
            created_at=timezone.now() - timedelta(days=8)
        )

        delete_old_rejected_friendship_requests()

        self.assertFalse(FriendshipRequest.objects.filter(pk=old.pk).exists())
        self.assertTrue(FriendshipRequest.objects.filter(pk=recent.pk).exists())
