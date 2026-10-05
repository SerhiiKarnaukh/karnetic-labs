import os
import shutil
import tempfile
from decimal import Decimal

from django.conf import settings
from django.test import TestCase, override_settings

from core.utils import create_active_user, create_test_image
from taberna_product.models import Category, Product, ReviewRating, Variation
from taberna_product.serializers import (
    CategorySerializer,
    ProductSerializer,
    ReviewRatingSerializer,
    VariationSerializer,
)
from taberna_profiles.models import UserProfile


@override_settings(
    MEDIA_ROOT=os.path.join(tempfile.gettempdir(), "taberna_product_serializers")
)
class ProductSerializersTest(TestCase):
    def setUp(self):
        self.user = create_active_user(
            email="serial-product@example.com",
            username="serial-product",
            password="pass123",
            first_name="Serial",
            last_name="Product",
        )
        self.profile = UserProfile.objects.create(user=self.user)
        self.category = Category.objects.create(name="Coffee", slug="serial-coffee")
        self.product = Product.objects.create(
            category=self.category,
            created_by=self.profile,
            name="Beans",
            slug="serial-beans",
            price=Decimal("9.99"),
            stock=4,
            stripe_product_id="prod_1",
        )

    def tearDown(self):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def test_serializers_return_expected_data(self):
        review = ReviewRating.objects.create(
            product=self.product,
            user=self.profile,
            subject="Good",
            rating=4,
        )
        variation = Variation.objects.create(
            product=self.product,
            variation_category="color",
            variation_value="Red",
        )

        self.assertEqual(ProductSerializer(self.product).data["name"], "Beans")
        self.assertEqual(
            CategorySerializer(self.category).data["products"][0]["id"],
            self.product.id,
        )
        self.assertEqual(
            ReviewRatingSerializer(review).data["user"],
            "Serial Product",
        )
        self.assertEqual(
            VariationSerializer(variation).data["variation_value"],
            "Red",
        )

    def test_creates_gallery_images(self):
        image = create_test_image("gallery.png")
        request = type("Request", (), {"FILES": {"image": image}})()
        view = type("View", (), {"request": request})()
        serializer = ProductSerializer(context={"view": view})

        product = serializer.create(
            {
                "category": self.category,
                "created_by": self.profile,
                "name": "Gallery product",
                "slug": "gallery-product",
                "price": Decimal("1"),
                "stock": 1,
            }
        )

        self.assertEqual(product.productgallery.count(), 1)
