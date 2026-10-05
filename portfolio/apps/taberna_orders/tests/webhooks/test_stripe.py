from unittest.mock import patch

from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse

from core.utils import create_active_user
from taberna_orders.models import Order
from taberna_orders.webhooks.stripe import handle_stripe_webhook
from taberna_profiles.models import UserProfile


class StripeWebhookTest(TestCase):
    def setUp(self):
        user = create_active_user(
            email="webhook@example.com",
            username="webhook",
            password="pass123",
            first_name="Web",
            last_name="Hook",
        )
        self.profile = UserProfile.objects.create(user=user)
        self.user = user

    @patch(
        "taberna_orders.webhooks.stripe.stripe.Webhook.construct_event",
        side_effect=__import__("stripe").error.StripeError("bad"),
    )
    def test_rejects_invalid_webhook(self, _):
        request = RequestFactory().post(
            "/",
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="signature",
        )
        response = handle_stripe_webhook(request)
        self.assertEqual(response.status_code, 400)

    @patch("taberna_orders.webhooks.stripe.send_order_email")
    @patch("taberna_orders.webhooks.stripe.stripe.Webhook.construct_event")
    def test_processes_completed_session(self, event, _):
        Order.objects.create(
            user=self.profile,
            order_number="webhook",
            first_name="A",
            last_name="B",
            phone="1",
            email=self.user.email,
            address_line_1="Street",
            country="US",
            state="CA",
            city="LA",
            order_total=1,
            tax=0,
            stripe_checkout_session_id="session",
        )
        event.return_value = {
            "type": "checkout.session.completed",
            "data": {"object": {"id": "session"}},
        }
        request = RequestFactory().post(
            "/",
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="signature",
        )
        self.assertEqual(handle_stripe_webhook(request).status_code, 200)

    @patch("taberna_orders.webhooks.stripe.stripe.Webhook.construct_event")
    def test_rejects_already_ordered_session(self, event):
        Order.objects.create(
            user=self.profile,
            order_number="ordered",
            first_name="A",
            last_name="B",
            phone="1",
            email=self.user.email,
            address_line_1="Street",
            country="US",
            state="CA",
            city="LA",
            order_total=1,
            tax=0,
            stripe_checkout_session_id="ordered-session",
            is_ordered=True,
        )
        event.return_value = {
            "type": "checkout.session.completed",
            "data": {"object": {"id": "ordered-session"}},
        }
        request = RequestFactory().post(
            "/",
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="signature",
        )
        self.assertEqual(handle_stripe_webhook(request).status_code, 400)

    @patch(
        "taberna_orders.views.webhook.handle_stripe_webhook",
        return_value=HttpResponse(status=200),
    )
    def test_webhook_view_delegates_to_handler(self, mock_handler):
        response = self.client.post(
            reverse("stripe_webhook"),
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="signature",
        )
        self.assertEqual(response.status_code, 200)
        mock_handler.assert_called_once()
