from decimal import Decimal
from django.test import TestCase
from core.utils import create_active_user
from taberna_product.models import Category, Product
from taberna_profiles.models import UserProfile


class CategoryApiViewsTest(TestCase):
    def test_category_endpoints(self):
        user = create_active_user(
            email="api-category@example.com",
            username="api-category",
            password="pass123",
            first_name="Api",
            last_name="Category",
        )
        profile = UserProfile.objects.create(user=user)
        category = Category.objects.create(name="Api", slug="api-category")
        Product.objects.create(category=category, created_by=profile, name="Beans", slug="category-beans", price=Decimal("3"), stock=1)
        self.assertEqual(self.client.get("/taberna-store/api/v1/products/api-category/").status_code, 200)
        self.assertEqual(self.client.get("/taberna-store/api/v1/products/missing/").status_code, 404)
        self.assertEqual(self.client.get("/taberna-store/api/v1/product-categories/").status_code, 200)
