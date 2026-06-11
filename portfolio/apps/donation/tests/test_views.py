from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from unittest.mock import patch, MagicMock
from decimal import Decimal

from donation.models import Donation


class MyDonationViewTest(TestCase):

    @patch("donation.views.checkout.choice")
    @patch("donation.views.checkout.stripe.checkout.Session.create")
    def test_my_donation_view_returns_expected_context(self, mock_stripe_create, mock_choice):
        # Mock Donation
        donation = Donation(title="Test Donation", amount=Decimal("12.34"))
        mock_choice.return_value = donation

        # Mock Stripe session
        mock_session = MagicMock()
        mock_session.id = "test_session_id"
        mock_stripe_create.return_value = mock_session

        response = self.client.get(reverse("my-donation"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "donation/includes/my-donation.html")

        self.assertIn("paypal_form", response.context)
        self.assertIn("session_id", response.context)
        self.assertIn("stripe_public_key", response.context)

        self.assertEqual(response.context["session_id"], "test_session_id")
        self.assertEqual(response.context["stripe_public_key"], settings.STRIPE_PUBLIC_KEY)

        paypal_form = response.context["paypal_form"]
        self.assertEqual(paypal_form.initial["amount"], donation.amount)
        self.assertEqual(paypal_form.initial["item_name"], donation.title)
        self.assertEqual(paypal_form.initial["business"], settings.PAYPAL_RECEIVER_EMAIL)

    @patch("donation.views.checkout.choice", side_effect=IndexError)
    @patch("donation.views.checkout.stripe.checkout.Session.create")
    def test_my_donation_fallback_if_no_donations(self, mock_stripe_create, mock_choice):
        mock_session = MagicMock()
        mock_session.id = "fallback_session_id"
        mock_stripe_create.return_value = mock_session

        response = self.client.get(reverse("my-donation"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "donation/includes/my-donation.html")

        paypal_form = response.context["paypal_form"]
        self.assertEqual(paypal_form.initial["amount"], 10)
        self.assertEqual(paypal_form.initial["item_name"], "Default Donation")


class PaymentSuccessViewTest(TestCase):

    @patch("donation.views.checkout.time.sleep")
    def test_payment_success_renders_correct_template(self, mock_sleep):
        response = self.client.get(reverse("payment-success"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "donation/includes/payment-success.html")

        mock_sleep.assert_called_once_with(10)


class PaymentFailedViewTest(TestCase):

    def test_payment_failed_renders_correct_template(self):
        response = self.client.get(reverse("payment-failed"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "donation/includes/payment-failed.html")
