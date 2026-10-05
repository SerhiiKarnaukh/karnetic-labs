from decimal import Decimal
from django.test import TestCase
from core.utils import create_active_user
from taberna_product.models import Category, Product, ReviewRating, Variation
from taberna_product.serializers import CategorySerializer, ProductSerializer, ReviewRatingSerializer, VariationSerializer
from taberna_profiles.models import UserProfile

class ProductSerializersTest(TestCase):
    def test_serializers_return_expected_data(self):
        user = create_active_user(email="serial-product@example.com", username="serial-product", password="pass123", first_name="Serial", last_name="Product")
        profile = UserProfile.objects.create(user=user)
        category = Category.objects.create(name="Coffee", slug="serial-coffee")
        product = Product.objects.create(category=category, created_by=profile, name="Beans", slug="serial-beans", price=Decimal("9.99"), stock=4, stripe_product_id="prod_1")
        review = ReviewRating.objects.create(product=product, user=profile, subject="Good", rating=4)
        variation = Variation.objects.create(product=product, variation_category="color", variation_value="Red")
        self.assertEqual(ProductSerializer(product).data["name"], "Beans")
        self.assertEqual(CategorySerializer(category).data["products"][0]["id"], product.id)
        self.assertEqual(ReviewRatingSerializer(review).data["user"], "Serial Product")
        self.assertEqual(VariationSerializer(variation).data["variation_value"], "Red")

    def test_creates_gallery_images(self):
        from core.utils import create_test_image
        from taberna_product.serializers import ProductSerializer
        image = create_test_image("gallery.png")
        request = type("Request", (), {"FILES": {"image": image}})()
        view = type("View", (), {"request": request})()
        category = Category.objects.create(name="Gallery", slug="gallery")
        user = create_active_user(email="gallery@example.com", username="gallery", password="pass123", first_name="Gallery", last_name="User")
        profile = UserProfile.objects.create(user=user)
        serializer = ProductSerializer(context={"view": view})
        product = serializer.create({"category": category, "created_by": profile, "name": "Gallery product", "slug": "gallery-product", "price": Decimal("1"), "stock": 1})
        self.assertEqual(product.productgallery.count(), 1)
