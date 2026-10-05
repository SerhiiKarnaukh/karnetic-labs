from decimal import Decimal
from unittest.mock import MagicMock, patch
from django.test import RequestFactory, TestCase
from core.utils import create_active_user
from taberna_cart.models import CartItem
from taberna_orders.forms import OrderForm
from taberna_orders.services.checkout import (
    clear_cart,
    create_order_from_form,
    create_order_products,
    create_payment,
    generate_order_number,
    stripe_session_create,
    update_order,
)
from taberna_product.models import Category, Product
from taberna_profiles.models import UserProfile


class CheckoutServicesTest(TestCase):
    def setUp(self):
        user = create_active_user(
            email="service@example.com",
            username="service",
            password="pass123",
            first_name="Service",
            last_name="User",
        )
        self.profile = UserProfile.objects.create(user=user)
        category = Category.objects.create(name="Service", slug="service")
        self.product = Product.objects.create(
            category=category,
            created_by=self.profile,
            name="Item",
            slug="service-item",
            price=Decimal("4"),
            stock=3,
            stripe_product_id="prod_1",
        )
        CartItem.objects.create(user=self.profile, product=self.product, quantity=2)

    def test_creates_order_payment_products_and_clears_cart(self):
        form = OrderForm(
            {
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
            }
        )
        self.assertTrue(form.is_valid())
        order = create_order_from_form(form, self.profile, 8, 0.16, RequestFactory().post("/"))
        order.order_number = generate_order_number(order)
        payment = create_payment(self.profile, "pay", "Stripe", "8", "Completed")
        update_order(order, payment)
        create_order_products(order, payment, self.profile)
        self.product.refresh_from_db()
        self.assertTrue(order.is_ordered)
        self.assertEqual(self.product.stock, 1)
        clear_cart(self.profile)
        self.assertFalse(CartItem.objects.exists())

    @patch("taberna_orders.services.checkout.stripe.checkout.Session.create")
    @patch("taberna_orders.services.checkout.stripe.Price.list")
    @patch("taberna_orders.services.checkout.get_tax_rate", return_value=None)
    def test_creates_stripe_session(self, _, prices, create):
        prices.return_value = MagicMock(data=[MagicMock(id="price_1")])
        create.return_value = MagicMock(id="session")
        session = stripe_session_create(CartItem.objects.all(), "service@example.com", "http://test")
        self.assertEqual(session.id, "session")

    @patch("taberna_orders.services.checkout.stripe.TaxRate.list")
    def test_get_tax_rate_and_email(self, tax_rates):
        from taberna_orders.services.checkout import get_tax_rate, send_order_email
        tax_rates.return_value = MagicMock(data=[MagicMock(display_name="VAT")])
        self.assertEqual(get_tax_rate().display_name, "VAT")
        order = type("Order", (), {"user": self.profile})()
        with patch("taberna_orders.services.checkout.EmailMessage.send"):
            send_order_email(order)

    @patch(
        "taberna_orders.services.checkout.stripe.TaxRate.list",
        side_effect=__import__("stripe").error.StripeError("bad"),
    )
    def test_returns_no_tax_rate_after_stripe_error(self, _):
        from taberna_orders.services.checkout import get_tax_rate
        self.assertIsNone(get_tax_rate())

    @patch("taberna_orders.services.checkout.stripe.Charge.create")
    def test_creates_stripe_charge(self, charge):
        from taberna_orders.services.checkout import stripe_charge_create
        request = type(
            "Request",
            (),
            {"data": {"stripe_token": "token"}, "user": type("User", (), {"email": "service@example.com"})()},
        )()
        order = type("Order", (), {"order_number": "1"})()
        stripe_charge_create(request, 12.5, order)
        self.assertTrue(charge.called)
