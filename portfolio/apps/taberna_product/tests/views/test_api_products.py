from decimal import Decimal
import os
import shutil
import tempfile

from django.conf import settings
from django.test import TestCase, override_settings

from core.utils import create_active_user, create_test_image
from taberna_product.models import Category, Product, Variation
from taberna_profiles.models import UserProfile


@override_settings(MEDIA_ROOT=os.path.join(tempfile.gettempdir(), "taberna_product_api"))
class ProductApiViewsTest(TestCase):
    def setUp(self):
        user = create_active_user(
            email="api-product@example.com",
            username="api-product",
            password="pass123",
            first_name="Api",
            last_name="Product",
        )
        profile = UserProfile.objects.create(user=user)
        self.category = Category.objects.create(name="Api", slug="api-product")
        self.product = Product.objects.create(
            category=self.category,
            created_by=profile,
            name="Beans",
            slug="beans",
            price=Decimal("3"),
            stock=1,
            stripe_product_id="prod_1",
            image=create_test_image("product.png"),
        )
        Variation.objects.create(
            product=self.product,
            variation_category="color",
            variation_value="Red",
        )

    def tearDown(self):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def test_product_endpoints(self):
        self.assertEqual(self.client.get("/taberna-store/api/v1/latest-products/").status_code, 200)
        self.assertEqual(self.client.get(f"/taberna-store/api/v1/products/{self.category.slug}/{self.product.slug}/").status_code, 200)
        self.assertEqual(self.client.post("/taberna-store/api/v1/products/search/", {"query": "Bean"}).status_code, 200)
        self.assertEqual(self.client.post("/taberna-store/api/v1/products/search/", {}).data, {"products": []})
