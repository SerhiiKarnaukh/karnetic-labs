from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient, APIRequestFactory

from core.utils import create_active_user
from taberna_cart.models import CartItem
from taberna_orders.models import Order
from taberna_orders.views.api.checkout import (
    OrderPaymentFailedAPIView,
    OrderPaymentSuccessAPIView,
)
from taberna_product.models import Category, Product
from taberna_profiles.models import UserProfile


class CheckoutApiViewsTest(TestCase):
    def test_charge_endpoint_requires_authentication(self):
        response = APIClient().post(
            reverse("taberna_api_place_order_charge"), {}, format="json"
        )
        self.assertEqual(response.status_code, 401)


class CheckoutApiBranchTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_active_user(
            email="order-api@example.com",
            username="order-api",
            password="pass123",
            first_name="Order",
            last_name="Api",
        )
        self.profile = UserProfile.objects.create(user=self.user)
        category = Category.objects.create(name="Order API", slug="order-api")
        self.product = Product.objects.create(
            category=category,
            created_by=self.profile,
            name="Item",
            slug="order-api-item",
            price=Decimal("4"),
            stock=3,
        )
        self.client.force_authenticate(self.user)
        self.data = {
            "first_name": "A",
            "last_name": "B",
            "phone": "1",
            "email": "a@b.com",
            "address_line_1": "Street",
            "address_line_2": "",
            "country": "US",
            "state": "CA",
            "city": "LA",
            "order_note": "",
            "stripe_token": "token",
        }

    def _add_cart_item(self):
        return CartItem.objects.create(
            user=self.profile, product=self.product, quantity=1
        )

    def test_charge_rejects_empty_cart(self):
        response = self.client.post(
            reverse("taberna_api_place_order_charge"), self.data, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "Your cart is empty!")

    def test_charge_rejects_invalid_form(self):
        self._add_cart_item()
        response = self.client.post(
            reverse("taberna_api_place_order_charge"),
            {"first_name": ""},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("errors", response.data)

    @patch("taberna_orders.views.api.checkout.stripe_charge_create", side_effect=Exception("card declined"))
    def test_charge_handles_stripe_exception(self, _):
        self._add_cart_item()
        response = self.client.post(
            reverse("taberna_api_place_order_charge"), self.data, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["errors"]["message"], "card declined")

    @patch("taberna_orders.views.api.checkout.send_order_email")
    @patch("taberna_orders.views.api.checkout.stripe_charge_create")
    def test_charge_checkout_success(self, _, __):
        self._add_cart_item()
        response = self.client.post(
            reverse("taberna_api_place_order_charge"), self.data, format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Order.objects.get().is_ordered)

    def test_session_rejects_empty_cart(self):
        response = self.client.post(
            reverse("taberna_api_place_order_session"),
            self.data,
            format="json",
            HTTP_ORIGIN="http://test",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "Your cart is empty!")

    def test_session_rejects_invalid_form(self):
        self._add_cart_item()
        response = self.client.post(
            reverse("taberna_api_place_order_session"),
            {"first_name": ""},
            format="json",
            HTTP_ORIGIN="http://test",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("errors", response.data)

    @patch(
        "taberna_orders.views.api.checkout.stripe_session_create",
        side_effect=Exception("session failed"),
    )
    def test_session_handles_stripe_exception(self, _):
        self._add_cart_item()
        response = self.client.post(
            reverse("taberna_api_place_order_session"),
            self.data,
            format="json",
            HTTP_ORIGIN="http://test",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["errors"]["message"], "session failed")

    @patch("taberna_orders.views.api.checkout.stripe_session_create")
    def test_session_checkout_success(self, create):
        self._add_cart_item()
        create.return_value = MagicMock(id="session", url="https://checkout")
        response = self.client.post(
            reverse("taberna_api_place_order_session"),
            self.data,
            format="json",
            HTTP_ORIGIN="http://test",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["checkout_url"], "https://checkout")

    @override_settings(DEBUG=False)
    def test_payment_success_forbidden_outside_debug(self):
        request = APIRequestFactory().post(
            "/", {"stripe_session_id": "success"}, format="json"
        )
        response = OrderPaymentSuccessAPIView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    @override_settings(DEBUG=True)
    def test_payment_success_rejects_already_ordered(self):
        Order.objects.create(
            user=self.profile,
            order_number="already",
            first_name="A",
            last_name="B",
            phone="1",
            email="a@b.com",
            address_line_1="Street",
            country="US",
            state="CA",
            city="LA",
            order_total=4,
            tax=0,
            stripe_checkout_session_id="already",
            is_ordered=True,
        )
        request = APIRequestFactory().post(
            "/", {"stripe_session_id": "already"}, format="json"
        )
        response = OrderPaymentSuccessAPIView.as_view()(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["message"], "Order already processed")

    @override_settings(DEBUG=True)
    @patch(
        "taberna_orders.views.api.checkout.create_payment",
        side_effect=Exception("payment boom"),
    )
    def test_payment_success_handles_exception(self, _):
        Order.objects.create(
            user=self.profile,
            order_number="boom",
            first_name="A",
            last_name="B",
            phone="1",
            email="a@b.com",
            address_line_1="Street",
            country="US",
            state="CA",
            city="LA",
            order_total=4,
            tax=0,
            stripe_checkout_session_id="boom",
        )
        request = APIRequestFactory().post(
            "/", {"stripe_session_id": "boom"}, format="json"
        )
        response = OrderPaymentSuccessAPIView.as_view()(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "payment boom")

    @override_settings(DEBUG=True)
    @patch("taberna_orders.views.api.checkout.send_order_email")
    def test_debug_payment_success_and_failure(self, _):
        Order.objects.create(
            user=self.profile,
            order_number="session-order",
            first_name="A",
            last_name="B",
            phone="1",
            email="a@b.com",
            address_line_1="Street",
            country="US",
            state="CA",
            city="LA",
            order_total=4,
            tax=0,
            stripe_checkout_session_id="success",
        )
        request = APIRequestFactory().post(
            "/", {"stripe_session_id": "success"}, format="json"
        )
        response = OrderPaymentSuccessAPIView.as_view()(request)
        self.assertEqual(response.status_code, 200)

        failed = Order.objects.create(
            user=self.profile,
            order_number="failed-order",
            first_name="A",
            last_name="B",
            phone="1",
            email="a@b.com",
            address_line_1="Street",
            country="US",
            state="CA",
            city="LA",
            order_total=4,
            tax=0,
            stripe_checkout_session_id="failed",
        )
        request = APIRequestFactory().post(
            "/", {"stripe_session_id": "failed"}, format="json"
        )
        self.assertEqual(OrderPaymentFailedAPIView.as_view()(request).status_code, 200)
        self.assertFalse(Order.objects.filter(pk=failed.pk).exists())

    @patch.object(Order, "delete", side_effect=Exception("cannot delete"))
    def test_payment_failed_handles_delete_exception(self, _):
        Order.objects.create(
            user=self.profile,
            order_number="delete-fail",
            first_name="A",
            last_name="B",
            phone="1",
            email="a@b.com",
            address_line_1="Street",
            country="US",
            state="CA",
            city="LA",
            order_total=4,
            tax=0,
            stripe_checkout_session_id="delete-fail",
        )
        request = APIRequestFactory().post(
            "/", {"stripe_session_id": "delete-fail"}, format="json"
        )
        response = OrderPaymentFailedAPIView.as_view()(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "cannot delete")
