from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from core.utils import create_active_user
from social_profiles.models import Profile
from social_posts.models import Comment, Post


class PostCreateCommentViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = create_active_user(
            email="user@example.com",
            username="testuser",
            password="testpass123",
            first_name="Test",
            last_name="User"
        )
        self.profile = Profile.objects.create(user=self.user)

        self.post = Post.objects.create(
            body="Test post",
            created_by=self.profile,
            is_private=False,
        )
        self.url = reverse("social_posts:post_create_comment", kwargs={"pk": self.post.pk})

    def test_authenticated_user_can_create_comment(self):
        self.client.force_authenticate(user=self.user)
        data = {"body": "Nice post!"}

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.first()
        self.assertEqual(comment.body, "Nice post!")
        self.assertEqual(comment.created_by, self.profile)
        self.post.refresh_from_db()
        self.assertEqual(self.post.comments_count, 1)

    def test_unauthenticated_user_cannot_create_comment(self):
        data = {"body": "Anonymous comment"}

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(Comment.objects.count(), 0)

    def test_empty_comment_body_is_allowed(self):
        self.client.force_authenticate(user=self.user)
        data = {"body": ""}

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.first()
        self.assertEqual(comment.body, "")
