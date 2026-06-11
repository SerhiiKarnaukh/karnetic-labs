import os

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from core.utils import create_active_user, create_test_image
from social_profiles.models import Profile
from social_posts.models import Post, PostAttachment


class PostCreateViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_active_user(
            email="user@example.com",
            username="user",
            password="pass123",
            first_name="Test",
            last_name="User",
        )
        self.profile = Profile.objects.create(user=self.user)
        self.client.force_authenticate(user=self.user)

        self.image = create_test_image("test-image.png")
        self.media_path = os.path.join(settings.MEDIA_ROOT, "social/posts")

    def tearDown(self):
        if os.path.exists(self.media_path):
            for f in os.listdir(self.media_path):
                os.remove(os.path.join(self.media_path, f))
            os.rmdir(self.media_path)

    def test_create_post_with_image(self):
        url = reverse("social_posts:post_create")
        data = {
            "body": "New post",
            "is_private": False,
            "images[0]": self.image
        }

        response = self.client.post(url, data=data, format="multipart")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(PostAttachment.objects.count(), 1)

        post = Post.objects.first()
        self.assertEqual(post.body, "New post")
        self.assertEqual(post.created_by, self.profile)
        self.assertEqual(post.attachments.count(), 1)

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.posts_count, 1)

    def test_create_post_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)

        url = reverse("social_posts:post_create")
        data = {
            "body": "Test post",
            "is_private": False,
        }

        response = self.client.post(url, data=data, format="multipart")

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json())
        self.assertEqual(response.json()["error"], "Authentication required")
        self.assertEqual(Post.objects.count(), 0)

    def test_create_post_with_invalid_body_returns_400(self):
        url = reverse("social_posts:post_create")
        data = {
            "body": "s",
            "is_private": False
        }

        response = self.client.post(url, data=data, format="multipart")

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
        self.assertEqual(response.json()["error"], "Form is not valid")
        self.assertEqual(Post.objects.count(), 0)
