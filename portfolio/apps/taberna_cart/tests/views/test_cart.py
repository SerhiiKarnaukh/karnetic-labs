from decimal import Decimal
import os
import tempfile
from django.test import TestCase, override_settings
from django.urls import reverse
from core.utils import create_active_user, create_test_image
from taberna_cart.models import CartItem
from taberna_product.models import Category, Product
from taberna_profiles.models import UserProfile


@override_settings(MEDIA_ROOT=os.path.join(tempfile.gettempdir(), "taberna_cart_views"))
class CartViewsTest(TestCase):
    def setUp(self):
        self.user = create_active_user(
            email="view@example.com", username="view", password="pass123", first_name="View", last_name="User"
        )
        self.profile = UserProfile.objects.create(user=self.user)
        category = Category.objects.create(name="View", slug="view")
        self.product = Product.objects.create(
            category=category,
            created_by=self.profile,
            name="Item",
            slug="view-item",
            price=Decimal("5"),
            stock=2,
            image=create_test_image("item.png"),
        )

    def test_guest_add_remove_and_cart_page(self):
        self.client.post(reverse("add_cart", args=[self.product.id]))
        item = CartItem.objects.get()
        self.assertEqual(self.client.get(reverse("cart")).status_code, 200)
        self.client.get(reverse("remove_cart", args=[self.product.id, item.id]))
        self.assertFalse(CartItem.objects.exists())

    def test_authenticated_add_and_checkout(self):
        self.client.force_login(self.user)
        self.client.post(reverse("add_cart", args=[self.product.id]))
        self.assertEqual(CartItem.objects.get().user, self.profile)
        self.assertEqual(self.client.get(reverse("checkout")).status_code, 200)

    def test_remove_views_ignore_missing_items(self):
        from unittest.mock import patch
        from taberna_cart.models import Cart
        with patch("taberna_cart.views.cart.get_cart_item", side_effect=Cart.DoesNotExist):
            self.assertEqual(self.client.get(reverse("remove_cart", args=[self.product.id, 99])).status_code, 302)
            self.assertEqual(self.client.get(reverse("remove_cart_item", args=[self.product.id, 99])).status_code, 302)

    def test_remove_decrements_then_deletes_item(self):
        self.client.force_login(self.user)
        item = CartItem.objects.create(user=self.profile, product=self.product, quantity=2)
        self.client.get(reverse("remove_cart", args=[self.product.id, item.id]))
        item.refresh_from_db()
        self.assertEqual(item.quantity, 1)
        self.client.get(reverse("remove_cart_item", args=[self.product.id, item.id]))
        self.assertFalse(CartItem.objects.exists())
