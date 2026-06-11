from django.test import TestCase
from django.urls import reverse

from social_posts.models import Trend


class GetTrendsViewTest(TestCase):
    def setUp(self):
        self.url = reverse('social_posts:get_trends')

    def test_returns_all_trends(self):
        Trend.objects.create(hashtag="#fitness", occurences=10)
        Trend.objects.create(hashtag="#health", occurences=5)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

        hashtags = [t["hashtag"] for t in response.json()]
        self.assertIn("#fitness", hashtags)
        self.assertIn("#health", hashtags)

    def test_returns_empty_list_if_no_trends(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
