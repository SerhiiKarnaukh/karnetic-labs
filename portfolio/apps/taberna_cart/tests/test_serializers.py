from decimal import Decimal
from django.test import TestCase
from core.utils import create_active_user
from taberna_cart.models import CartItem
from taberna_cart.serializers import CartItemSerializer
from taberna_product.models import Category, Product, Variation
from taberna_profiles.models import UserProfile


class CartSerializerTest(TestCase):
    def test_serializes_item_and_variations(self):
        user = create_active_user(
            email="serializer@example.com",
            username="serializer",
            password="pass123",
            first_name="Serial",
            last_name="User",
        )
        profile = UserProfile.objects.create(user=user)
        category = Category.objects.create(name="Tea", slug="serializer-tea")
        product = Product.objects.create(
            category=category, created_by=profile, name="Tea", slug="serializer-product", price=Decimal("4.50"), stock=1
        )
        variation = Variation.objects.create(product=product, variation_category="size", variation_value="Large")
        item = CartItem.objects.create(user=profile, product=product, quantity=2)
        item.variations.add(variation)
        self.assertEqual(CartItemSerializer(item).data["sub_total"], Decimal("9.00"))
