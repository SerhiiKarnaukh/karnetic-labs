from decimal import Decimal
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from core.utils import create_active_user
from taberna_cart.context_processors import counter
from taberna_cart.models import CartItem
from taberna_product.models import Category, Product
from taberna_profiles.models import UserProfile

class CartCounterTest(TestCase):
    def test_counts_user_items_and_skips_admin(self):
        user = create_active_user(email="counter@example.com", username="counter", password="pass123", first_name="Counter", last_name="User")
        profile = UserProfile.objects.create(user=user)
        category = Category.objects.create(name="Counter", slug="counter")
        product = Product.objects.create(category=category, created_by=profile, name="Item", slug="counter-item", price=Decimal("1"), stock=1)
        CartItem.objects.create(user=profile, product=product, quantity=3)
        request = RequestFactory().get("/")
        SessionMiddleware(lambda request: None).process_request(request)
        request.session.save()
        request.user = user
        self.assertEqual(counter(request), {"cart_count": 3})
        request.path = "/admin/"
        self.assertEqual(counter(request), {})

    def test_returns_zero_when_cart_lookup_fails(self):
        request = RequestFactory().get("/")
        SessionMiddleware(lambda request: None).process_request(request)
        request.session.save()
        request.user = type("Guest", (), {"is_authenticated": False})()
        from unittest.mock import patch
        from taberna_cart.models import Cart
        with patch("taberna_cart.context_processors.Cart.objects.filter", side_effect=Cart.DoesNotExist):
            self.assertEqual(counter(request), {"cart_count": 0})
