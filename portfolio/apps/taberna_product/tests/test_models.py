from decimal import Decimal
from django.test import TestCase
from core.utils import create_active_user
from taberna_product.models import Category, Product, ReviewRating, Variation
from taberna_profiles.models import UserProfile

class ProductModelsTest(TestCase):
    def setUp(self):
        user = create_active_user(email="product@example.com", username="product", password="pass123", first_name="Product", last_name="User")
        self.profile = UserProfile.objects.create(user=user)
        self.category = Category.objects.create(name="Coffee", slug="coffee")
        self.product = Product.objects.create(category=self.category, created_by=self.profile, name="Beans", slug="beans", price=Decimal("9.99"), stock=4)

    def test_models_urls_reviews_and_variations(self):
        review = ReviewRating.objects.create(product=self.product, user=self.profile, subject="Good", rating=4)
        color = Variation.objects.create(product=self.product, variation_category="color", variation_value="Red")
        size = Variation.objects.create(product=self.product, variation_category="size", variation_value="Large")
        self.assertEqual(str(self.category), "Coffee")
        self.assertEqual(self.category.get_absolute_url(), "/taberna-store/category/coffee/")
        self.assertEqual(self.product.get_absolute_url(), "/taberna-store/category/coffee/beans/")
        self.assertEqual(self.product.averageReview(), 4.0)
        self.assertEqual(self.product.countReview(), 1)
        self.assertEqual(list(Variation.objects.colors()), [color])
        self.assertEqual(list(Variation.objects.sizes()), [size])
        self.assertEqual(str(review), "Good")

    def test_empty_reviews_and_model_strings(self):
        from taberna_product.models import ProductGallery
        product = Product.objects.create(category=self.category, created_by=self.profile, name="Other", slug="other", price=Decimal("1"), stock=1)
        variation = Variation.objects.create(product=product, variation_category="color", variation_value="Blue")
        gallery = ProductGallery.objects.create(product=product, image="gallery.png")
        self.assertEqual(str(product), "Other")
        self.assertEqual(str(variation), "Blue")
        self.assertEqual(str(gallery), "Other")
        self.assertEqual(product.averageReview(), 0)
        self.assertEqual(product.countReview(), 0)
