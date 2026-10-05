from unittest.mock import MagicMock, patch

from django.conf import settings
from django.test import TestCase, override_settings
from paypal.standard.models import ST_PP_COMPLETED

from taberna_orders.models import Order
from taberna_orders.signals.orders import paypal_taberna_payment_received


class OrderSignalsTest(TestCase):
    @patch("taberna_orders.signals.orders.Order.objects.get", side_effect=Order.DoesNotExist)
    def test_ignores_missing_order(self, _):
        sender = type("IPN", (), {"invoice": "missing", "txn_id": "txn"})()
        self.assertIsNone(paypal_taberna_payment_received(sender))

    def test_ignores_non_completed_payment_status(self):
        order = MagicMock()
        sender = type(
            "IPN",
            (),
            {
                "invoice": "1",
                "txn_id": "txn",
                "payment_status": "Pending",
                "receiver_email": "merchant@example.com",
            },
        )()
        with patch("taberna_orders.signals.orders.Order.objects.get", return_value=order):
            self.assertIsNone(paypal_taberna_payment_received(sender))

    @override_settings(PAYPAL_RECEIVER_EMAIL="merchant@example.com")
    def test_ignores_invalid_receiver_email(self):
        order = MagicMock()
        sender = type(
            "IPN",
            (),
            {
                "invoice": "1",
                "txn_id": "txn",
                "payment_status": ST_PP_COMPLETED,
                "receiver_email": "attacker@example.com",
            },
        )()
        with patch("taberna_orders.signals.orders.Order.objects.get", return_value=order):
            self.assertIsNone(paypal_taberna_payment_received(sender))

    @override_settings(PAYPAL_RECEIVER_EMAIL="merchant@example.com")
    @patch("taberna_orders.signals.orders.send_order_email")
    @patch("taberna_orders.signals.orders.clear_cart")
    @patch("taberna_orders.signals.orders.create_order_products")
    @patch("taberna_orders.signals.orders.update_order")
    @patch("taberna_orders.signals.orders.create_payment")
    def test_processes_completed_payment(
        self, create_payment, update, products, clear, email
    ):
        order = MagicMock(order_total=5, user=MagicMock())
        sender = type(
            "IPN",
            (),
            {
                "invoice": "1",
                "txn_id": "txn",
                "payment_status": ST_PP_COMPLETED,
                "receiver_email": settings.PAYPAL_RECEIVER_EMAIL,
            },
        )()
        with patch("taberna_orders.signals.orders.Order.objects.get", return_value=order):
            paypal_taberna_payment_received(sender)
        self.assertTrue(create_payment.called)
        self.assertTrue(email.called)

    @override_settings(PAYPAL_RECEIVER_EMAIL="merchant@example.com")
    @patch(
        "taberna_orders.signals.orders.create_payment",
        side_effect=Exception("processing failed"),
    )
    def test_handles_processing_exception(self, _):
        order = MagicMock(order_total=5, user=MagicMock())
        sender = type(
            "IPN",
            (),
            {
                "invoice": "1",
                "txn_id": "txn",
                "payment_status": ST_PP_COMPLETED,
                "receiver_email": settings.PAYPAL_RECEIVER_EMAIL,
            },
        )()
        with patch("taberna_orders.signals.orders.Order.objects.get", return_value=order):
            self.assertIsNone(paypal_taberna_payment_received(sender))
