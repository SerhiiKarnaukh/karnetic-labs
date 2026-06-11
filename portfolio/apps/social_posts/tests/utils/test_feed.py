from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from core.utils import create_active_user
from social_posts.models import Post
from social_posts.utils import get_user_feed_posts
from social_profiles.models import Profile


class GetUserFeedPostsTest(TestCase):
    def test_unauthenticated_user_gets_only_public_posts(self):
        public_post = Post.objects.create(body="Public", is_private=False, created_by=Profile.objects.create(user=create_active_user(
            email="public@example.com",
            username="publicuser",
            password="testpass123",
            first_name="Public",
            last_name="User"
        )))
        private_post = Post.objects.create(body="Private", is_private=True, created_by=Profile.objects.create(user=create_active_user(
            email="private@example.com",
            username="privateuser",
            password="testpass123",
            first_name="Private",
            last_name="User"
        )))

        result = get_user_feed_posts(AnonymousUser())

        self.assertIn(public_post, result)
        self.assertNotIn(private_post, result)

    def test_authenticated_user_gets_own_posts(self):
        user = create_active_user(
            email="user@example.com",
            username="user",
            password="testpass123",
            first_name="User",
            last_name="Test"
        )
        profile = Profile.objects.create(user=user)

        own_post = Post.objects.create(body="Own", is_private=True, created_by=profile)
        someone_else = Profile.objects.create(user=create_active_user(
            email="someone@example.com",
            username="someone",
            password="testpass123",
            first_name="Someone",
            last_name="Else"
        ))
        other_post = Post.objects.create(body="Other", is_private=True, created_by=someone_else)

        result = get_user_feed_posts(user)

        self.assertIn(own_post, result)
        self.assertNotIn(other_post, result)

    def test_authenticated_user_gets_own_and_friends_posts(self):
        user = create_active_user(
            email="user@example.com",
            username="user",
            password="testpass123",
            first_name="User",
            last_name="Test"
        )
        profile = Profile.objects.create(user=user)

        friend_user = create_active_user(
            email="friend@example.com",
            username="frienduser",
            password="testpass123",
            first_name="Friend",
            last_name="User"
        )
        friend_profile = Profile.objects.create(user=friend_user)

        profile.friends.add(friend_profile)

        own_post = Post.objects.create(body="Own", is_private=True, created_by=profile)
        friend_post = Post.objects.create(body="Friend", is_private=True, created_by=friend_profile)

        result = get_user_feed_posts(user)

        self.assertIn(own_post, result)
        self.assertIn(friend_post, result)

    def test_authenticated_user_without_profile_gets_only_public_posts(self):
        user = create_active_user(
            email="noprof@example.com",
            username="noprof",
            password="testpass123",
            first_name="No",
            last_name="Profile"
        )

        public_post = Post.objects.create(body="Public", is_private=False, created_by=Profile.objects.create(user=create_active_user(
            email="some@example.com",
            username="some",
            password="pass123",
            first_name="Some",
            last_name="User"
        )))
        private_post = Post.objects.create(body="Private", is_private=True, created_by=Profile.objects.create(user=create_active_user(
            email="hidden@example.com",
            username="hidden",
            password="pass123",
            first_name="Hidden",
            last_name="User"
        )))

        result = get_user_feed_posts(user)

        self.assertIn(public_post, result)
        self.assertNotIn(private_post, result)
