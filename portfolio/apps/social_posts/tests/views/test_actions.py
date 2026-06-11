import os

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from core.utils import create_active_user, create_test_image
from social_profiles.models import Profile
from social_posts.models import Like, Post, PostAttachment


class PostLikeViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.author_user = create_active_user(username="author",
                                              email="author@example.com",
                                              password="pass123",
                                              first_name="Test_author",
                                              last_name="User_author")
        self.liker_user = create_active_user(username="liker",
                                             email="liker@example.com",
                                             password="pass123",
                                             first_name="Test_liker",
                                             last_name="User_liker")

        self.author_profile = Profile.objects.create(user=self.author_user)
        self.liker_profile = Profile.objects.create(user=self.liker_user)

        self.post = Post.objects.create(
            body="Test Post", created_by=self.author_profile, is_private=False
        )

        self.like_url = reverse("social_posts:post_like", kwargs={"pk": self.post.pk})

    def test_authenticated_user_can_like_post(self):
        self.client.force_authenticate(user=self.liker_user)

        response = self.client.post(self.like_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "like created")
        self.assertEqual(Like.objects.count(), 1)
        self.assertEqual(self.post.likes.count(), 1)
        self.post.refresh_from_db()
        self.assertEqual(self.post.likes_count, 1)

    def test_user_cannot_like_twice(self):
        self.client.force_authenticate(user=self.liker_user)

        self.client.post(self.like_url)
        response = self.client.post(self.like_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "post already liked")
        self.assertEqual(Like.objects.count(), 1)
        self.assertEqual(self.post.likes.count(), 1)

    def test_unauthenticated_user_cannot_like(self):
        response = self.client.post(self.like_url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Like.objects.count(), 0)

    def test_user_likes_own_post_creates_like_but_no_error(self):
        self.client.force_authenticate(user=self.author_user)

        response = self.client.post(self.like_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "like created")
        self.assertEqual(Like.objects.count(), 1)
        self.assertEqual(self.post.likes.count(), 1)


class PostDeleteViewTest(TestCase):

    def setUp(self):
        self.user = create_active_user(
            email="user@example.com",
            username="testuser",
            password="123456",
            first_name="Test",
            last_name="User"
        )
        self.client.login(email="user@example.com", password="123456")
        self.profile = Profile.objects.create(user=self.user)

        self.image = create_test_image("test-image.jpg")

        self.attachment = PostAttachment.objects.create(
            image=self.image,
            created_by=self.profile
        )
        self.post = Post.objects.create(
            body="Test post",
            created_by=self.profile
        )

        self.profile.posts_count = 1
        self.profile.save()

        self.post.attachments.add(self.attachment)
        self.post.save()

        self.url = reverse("social_posts:post_delete", kwargs={"pk": self.post.id})

    def tearDown(self):
        media_root = settings.MEDIA_ROOT
        if os.path.exists(media_root):
            for root, dirs, files in os.walk(media_root, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(media_root)

    def test_authenticated_user_can_delete_own_post(self):
        initial_posts_count = self.profile.posts.count()

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "post deleted"})
        self.assertEqual(Post.objects.count(), 0)
        self.assertEqual(PostAttachment.objects.count(), 0)

        self.assertFalse(os.path.isfile(self.attachment.image.path))

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.posts_count, initial_posts_count - 1)

    def test_unauthenticated_user_cannot_delete_post(self):
        self.client.logout()
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 401)

    def test_user_cannot_delete_someone_elses_post(self):
        other_user = create_active_user(
            email="other@example.com",
            username="otheruser",
            password="123456",
            first_name="otherTest",
            last_name="otherUser"
        )
        Profile.objects.create(user=other_user)

        self.client.logout()
        self.client.force_login(other_user)

        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 404)


class PostReportViewTest(TestCase):
    def setUp(self):
        self.user = create_active_user(
            email="user@example.com",
            username="testuser",
            password="testpass123",
            first_name="Test",
            last_name="User"
        )
        self.profile = Profile.objects.create(user=self.user)

        self.client.force_login(self.user)

        self.post = Post.objects.create(
            body="Test post",
            created_by=self.profile
        )

        self.url = reverse("social_posts:post_report", kwargs={"pk": self.post.pk})

    def test_authenticated_user_can_report_post(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "post reported"})
        self.assertIn(self.profile, self.post.reported_by_users.all())

    def test_unauthenticated_user_cannot_report_post(self):
        self.client.logout()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)

    def test_multiple_reports_by_same_user_dont_duplicate(self):
        self.client.post(self.url)
        self.client.post(self.url)

        self.post.refresh_from_db()

        self.assertEqual(self.post.reported_by_users.filter(pk=self.profile.pk).count(), 1)
