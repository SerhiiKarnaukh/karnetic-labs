from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from core.utils import create_active_user
from social_posts.models import Post, Trend
from social_posts.tasks.trends import create_social_posts_trends
from social_profiles.models import Profile


class CreateSocialPostsTrendsTaskTests(TestCase):
    def setUp(self):
        user = create_active_user(
            email='trends@example.com',
            username='trends',
            password='testpass123',
            first_name='Trend',
            last_name='User',
        )
        self.profile = Profile.objects.create(user=user)

    def create_post(self, body, is_private=False):
        return Post.objects.create(
            body=body, is_private=is_private, created_by=self.profile
        )

    def test_creates_public_hashtag_trends_and_ignores_private_posts(self):
        self.create_post('#Python #Django!')
        self.create_post('Another #python post')
        self.create_post('#private', is_private=True)
        Trend.objects.create(hashtag='old', occurences=1)

        create_social_posts_trends()

        trends = {trend.hashtag: trend.occurences for trend in Trend.objects.all()}
        self.assertEqual(trends, {'python': 2, 'django': 1})

    def test_uses_recent_public_posts_when_last_day_is_empty(self):
        post = self.create_post('#Fallback!')
        Post.objects.filter(pk=post.pk).update(
            created_at=timezone.now() - timedelta(days=2)
        )

        create_social_posts_trends()

        self.assertEqual(
            Trend.objects.get(hashtag='fallback').occurences, 1
        )
