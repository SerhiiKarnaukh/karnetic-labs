from decimal import Decimal

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase

from core.utils import create_active_user
from taberna_cart.models import Cart, CartItem
from taberna_product.models import Category, Product
from taberna_profiles.models import UserProfile
from taberna_profiles.utils.profile import (
    handle_cart_after_login,
    redirect_to_next_or_dashboard,
)


class ProfileUtilsTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = create_active_user(
            email="utils@example.com",
            username="utils",
            password="pass123",
            first_name="Utils",
            last_name="User",
        )
        self.profile = UserProfile.objects.create(user=self.user)
        category = Category.objects.create(name="Utils", slug="utils")
        self.product = Product.objects.create(
            category=category,
            created_by=self.profile,
            name="Item",
            slug="utils-item",
            price=Decimal("1"),
            stock=5,
        )

    def _session_request(self, path="/", **extra):
        request = self.factory.get(path, **extra)
        SessionMiddleware(lambda request: None).process_request(request)
        request.session.save()
        return request

    def test_redirects_to_next_or_dashboard(self):
        request = self.factory.get("/", HTTP_REFERER="http://test/?next=/target/")
        self.assertEqual(redirect_to_next_or_dashboard(request).url, "/target/")
        self.assertEqual(
            redirect_to_next_or_dashboard(self.factory.get("/")).url,
            "/taberna-profiles/",
        )

    def test_handles_missing_guest_cart_and_bad_referer(self):
        request = self._session_request("/", HTTP_REFERER="not-a-url")
        self.assertIsNone(handle_cart_after_login(request, self.profile))
        self.assertEqual(redirect_to_next_or_dashboard(request).url, "/taberna-profiles/")

    def test_moves_guest_cart_to_profile(self):
        request = self._session_request("/")
        cart = Cart.objects.create(cart_id=request.session.session_key)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=1)

        handle_cart_after_login(request, self.profile)

        item.refresh_from_db()
        self.assertEqual(item.user, self.profile)

    def test_uses_cart_id_from_request_data(self):
        from unittest.mock import MagicMock

        cart = Cart.objects.create(cart_id="guest-cart")
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        request = MagicMock()
        request.query_params = {}
        request.data = {"cart_id": cart.id}

        handle_cart_after_login(request, self.profile)

        item = CartItem.objects.get(product=self.product)
        self.assertEqual(item.user, self.profile)

    def test_returns_early_for_empty_cart(self):
        request = self._session_request("/")
        Cart.objects.create(cart_id=request.session.session_key)

        self.assertIsNone(handle_cart_after_login(request, self.profile))

    def test_merges_matching_variation_quantities(self):
        request = self._session_request("/")
        cart = Cart.objects.create(cart_id=request.session.session_key)
        guest_item = CartItem.objects.create(
            cart=cart, product=self.product, quantity=1
        )
        user_item = CartItem.objects.create(
            user=self.profile, product=self.product, quantity=2
        )

        handle_cart_after_login(request, self.profile)

        user_item.refresh_from_db()
        self.assertEqual(user_item.quantity, 3)
        guest_item.refresh_from_db()
        self.assertIsNone(guest_item.user)
