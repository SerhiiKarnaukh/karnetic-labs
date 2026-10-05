from decimal import Decimal
import os
import tempfile
from django.test import TestCase, override_settings
from django.urls import reverse
from core.utils import create_active_user, create_test_image
from taberna_product.models import Category, Product
from taberna_profiles.models import UserProfile


@override_settings(MEDIA_ROOT=os.path.join(tempfile.gettempdir(), "taberna_storefront"))
class StorefrontViewsTest(TestCase):
    def setUp(self):
        user = create_active_user(
            email="store@example.com",
            username="store",
            password="pass123",
            first_name="Store",
            last_name="User",
        )
        profile = UserProfile.objects.create(user=user)
        self.category = Category.objects.create(name="Store", slug="store", cat_image=create_test_image("category.png"))
        self.product = Product.objects.create(
            category=self.category,
            created_by=profile,
            name="Coffee Beans",
            slug="coffee-beans",
            price=Decimal("3"),
            stock=1,
            image=create_test_image("product.png"),
        )

    def test_storefront_pages(self):
        urls = [
            reverse("frontpage"),
            reverse("store"),
            reverse("category_detail", args=[self.category.slug]),
            reverse("product_detail", args=[self.category.slug, self.product.slug]),
            reverse("search") + "?keyword=Coffee",
            reverse("contact"),
            reverse("about"),
        ]
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_search_without_keyword_is_empty(self):
        response = self.client.get(reverse("search"))
        self.assertEqual(list(response.context["products"]), [])
