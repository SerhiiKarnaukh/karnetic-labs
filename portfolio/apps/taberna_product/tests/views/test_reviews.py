from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from core.utils import create_active_user
from taberna_product.models import Category, Product, ReviewRating
from taberna_profiles.models import UserProfile


class ReviewViewsTest(TestCase):
    def setUp(self):
        self.user = create_active_user(
            email="review@example.com",
            username="review",
            password="pass123",
            first_name="Review",
            last_name="User",
        )
        self.profile = UserProfile.objects.create(user=self.user)
        category = Category.objects.create(name="Review", slug="review")
        self.product = Product.objects.create(
            category=category, created_by=self.profile, name="Item", slug="review-item", price=Decimal("1"), stock=1
        )

    def test_creates_and_updates_review(self):
        self.client.force_login(self.user)
        url = reverse("submit_review", args=[self.product.id])
        self.client.post(url, {"subject": "Great", "review": "Nice", "rating": 5}, HTTP_REFERER="/")
        self.assertEqual(ReviewRating.objects.count(), 1)
        self.client.post(url, {"subject": "Better", "review": "Nice", "rating": 4}, HTTP_REFERER="/")
        self.assertEqual(ReviewRating.objects.get().subject, "Better")
