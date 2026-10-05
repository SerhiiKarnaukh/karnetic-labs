from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.http import HttpResponse
from django.test import TestCase, override_settings
from django.urls import reverse

from core.utils import create_active_user
from paypal.standard.ipn.models import PayPalIPN
from taberna_cart.models import CartItem
from taberna_orders.models import Order, OrderProduct, Payment
from taberna_product.models import Category, Product
from taberna_profiles.models import UserProfile


class CheckoutViewsTest(TestCase):
    def setUp(self):
        self.user = create_active_user(
            email="checkout@example.com",
            username="checkout",
            password="pass123",
            first_name="Check",
            last_name="Out",
        )
        self.profile = UserProfile.objects.create(user=self.user)
        category = Category.objects.create(name="Checkout", slug="checkout")
        self.product = Product.objects.create(
            category=category,
            created_by=self.profile,
            name="Checkout Item",
            slug="checkout-item",
            price=Decimal("10"),
            stock=5,
        )
        self.order_data = {
            "first_name": "Check",
            "last_name": "Out",
            "phone": "123",
            "email": "checkout@example.com",
            "address_line_1": "Street 1",
            "address_line_2": "",
            "country": "US",
            "state": "CA",
            "city": "LA",
            "order_note": "",
        }

    def test_failed_order_page_and_empty_cart_redirect(self):
        self.assertEqual(self.client.get(reverse("order_failed")).status_code, 200)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("place_order")).status_code, 302)

    def test_place_order_get_with_cart_redirects_to_checkout(self):
        CartItem.objects.create(user=self.profile, product=self.product, quantity=1)
        self.client.force_login(self.user)

        response = self.client.get(reverse("place_order"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("checkout"))

    @override_settings(PAYPAL_RECEIVER_EMAIL="merchant@example.com", DEBUG=False)
    @patch("taberna_orders.views.checkout.render")
    @patch("taberna_orders.views.checkout.PayPalPaymentsForm")
    def test_place_order_post_valid_renders_payments(self, mock_form, mock_render):
        mock_form.return_value = MagicMock()
        mock_render.return_value = HttpResponse("payments")
        CartItem.objects.create(user=self.profile, product=self.product, quantity=2)
        self.client.force_login(self.user)

        response = self.client.post(reverse("place_order"), self.order_data)

        self.assertEqual(response.status_code, 200)
        mock_render.assert_called_once()
        self.assertEqual(
            mock_render.call_args.args[1], "taberna_orders/payments.html"
        )
        self.assertTrue(Order.objects.filter(user=self.profile).exists())

    def test_place_order_post_invalid_redirects_to_checkout(self):
        CartItem.objects.create(user=self.profile, product=self.product, quantity=1)
        self.client.force_login(self.user)

        response = self.client.post(reverse("place_order"), {"first_name": ""})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("checkout"))

    @patch(
        "taberna_orders.views.checkout.render",
        return_value=HttpResponse("order complete"),
    )
    @patch("time.sleep")
    def test_order_complete_renders_success_page(self, mock_sleep, mock_render):
        order = Order.objects.create(
            user=self.profile,
            order_number="12345",
            first_name="Check",
            last_name="Out",
            phone="123",
            email=self.user.email,
            address_line_1="Street",
            country="US",
            state="CA",
            city="LA",
            order_total=20,
            tax=2,
            is_ordered=True,
        )
        payment = Payment.objects.create(
            user=self.profile,
            payment_id="txn-123",
            payment_method="PayPal",
            amount_paid="20",
            status="Completed",
        )
        order.payment = payment
        order.save()
        OrderProduct.objects.create(
            order=order,
            payment=payment,
            user=self.profile,
            product=self.product,
            quantity=2,
            product_price=10,
            ordered=True,
        )
        PayPalIPN.objects.create(invoice="12345", txn_id="txn-123")

        response = self.client.get(reverse("order_complete", args=[12345]))

        self.assertEqual(response.status_code, 200)
        mock_render.assert_called_once()
        self.assertEqual(
            mock_render.call_args.args[1], "taberna_orders/order_complete.html"
        )
        mock_sleep.assert_called_once_with(10)

    @patch(
        "taberna_orders.views.checkout.redirect",
        return_value=HttpResponse(status=302),
    )
    @patch("time.sleep")
    def test_order_complete_missing_payment_redirects_home(self, mock_sleep, mock_redirect):
        Order.objects.create(
            user=self.profile,
            order_number="99999",
            first_name="Check",
            last_name="Out",
            phone="123",
            email=self.user.email,
            address_line_1="Street",
            country="US",
            state="CA",
            city="LA",
            order_total=20,
            tax=2,
            is_ordered=True,
        )
        PayPalIPN.objects.create(invoice="99999", txn_id="missing-txn")

        response = self.client.get(reverse("order_complete", args=[99999]))

        self.assertEqual(response.status_code, 302)
        mock_redirect.assert_called_once_with("home")
        mock_sleep.assert_called_once_with(10)
