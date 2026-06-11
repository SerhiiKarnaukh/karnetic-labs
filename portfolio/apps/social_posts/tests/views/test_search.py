from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from core.utils import create_active_user
from social_profiles.models import Profile
from social_posts.models import Post


class SearchApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = create_active_user(
            email='test@example.com',
            username='testuser',
            password='pass123',
            first_name='John',
            last_name='Doe'
        )
        self.profile = Profile.objects.create(user=self.user)
        self.client.force_authenticate(self.user)

        self.friend = create_active_user(
            email='friend@example.com',
            username='frienduser',
            password='pass123',
            first_name='Jane',
            last_name='Smith'
        )
        self.friend_profile = Profile.objects.create(user=self.friend)
        self.profile.friends.add(self.friend_profile)

        self.public_post = Post.objects.create(
            body='This is a public post about Django',
            is_private=False,
            created_by=self.friend_profile
        )
        self.private_post = Post.objects.create(
            body='Secret post from friend',
            is_private=True,
            created_by=self.friend_profile
        )
        self.own_post = Post.objects.create(
            body='My own private Django post',
            is_private=True,
            created_by=self.profile
        )

    def test_search_profiles_get(self):
        url = reverse("social_posts:search") + "?query=Jane"
        response = self.client.get(url)
        results = response.data["results"]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(results['profiles']), 1)
        self.assertEqual(results['profiles'][0]['first_name'], 'Jane')

    def test_search_profiles_post(self):
        url = reverse("social_posts:search")
        response = self.client.post(url, {"query": "Jane"}, format="json")
        results = response.data["results"]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(results['profiles']), 1)

    def test_search_posts_public_and_friends(self):
        url = reverse("social_posts:search") + "?query=Django"
        response = self.client.get(url)
        results = response.data["results"]
        post_bodies = [p["body"] for p in results["posts"]]
        self.assertIn(self.public_post.body, post_bodies)
        self.assertIn(self.own_post.body, post_bodies)
        self.assertNotIn(self.private_post.body, post_bodies)

    def test_search_returns_empty(self):
        url = reverse("social_posts:search") + "?query=NothingMatches"
        response = self.client.get(url)
        results = response.data["results"]
        self.assertEqual(len(results['profiles']), 0)
        self.assertEqual(len(results['posts']), 0)

    def test_search_pagination(self):
        for i in range(10):
            Post.objects.create(body=f"Post {i} Django", is_private=False, created_by=self.friend_profile)

        url = reverse("social_posts:search") + "?query=Django&page_size=5"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.data)
        self.assertLessEqual(len(response.data["results"]["posts"]), 5)
