from django.test import TestCase, override_settings
from unittest.mock import Mock, patch
from donation.models import Donation, Transaction
from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received
from decimal import Decimal


class PaypalIPNSignalTest(TestCase):

    def setUp(self):
        self.donation = Donation.objects.create(
            title="Test Donation",
            amount=12.34
        )

        self.valid_ipn_data = {
            'payment_status': ST_PP_COMPLETED,
            'receiver_email': 'merchant@example.com',
            'mc_gross': self.donation.amount,
            'mc_currency': 'USD',
            'invoice': 'INV12345',
            'item_name': self.donation.title,
        }

    @override_settings(PAYPAL_RECEIVER_EMAIL='merchant@example.com')
    @patch('donation.signals.paypal.choice')
    def test_transaction_created_on_valid_ipn(self, mock_choice):
        mock_choice.return_value = self.donation

        ipn_mock = Mock(**self.valid_ipn_data)
        valid_ipn_received.send(sender=ipn_mock)

        self.assertEqual(Transaction.objects.count(), 1)
        transaction = Transaction.objects.first()
        self.assertEqual(transaction.invoice, ipn_mock.invoice)
        self.assertEqual(transaction.title, ipn_mock.item_name)
        self.assertEqual(transaction.amount, Decimal(str(ipn_mock.mc_gross)))
        self.assertTrue(transaction.paid)

    @override_settings(PAYPAL_RECEIVER_EMAIL='merchant@example.com')
    def test_no_transaction_if_receiver_email_mismatch(self):
        ipn_mock = Mock(**{**self.valid_ipn_data, 'receiver_email': 'attacker@example.com'})

        valid_ipn_received.send(sender=ipn_mock)

        self.assertEqual(Transaction.objects.count(), 0)

    @override_settings(PAYPAL_RECEIVER_EMAIL='merchant@example.com')
    def test_no_transaction_if_amount_does_not_match(self):
        ipn_mock = Mock(**{**self.valid_ipn_data, 'mc_gross': 99.99})

        valid_ipn_received.send(sender=ipn_mock)

        self.assertEqual(Transaction.objects.count(), 0)

    @override_settings(PAYPAL_RECEIVER_EMAIL='merchant@example.com')
    def test_no_transaction_if_currency_does_not_match(self):
        ipn_mock = Mock(**{**self.valid_ipn_data, 'mc_currency': 'EUR'})

        valid_ipn_received.send(sender=ipn_mock)

        self.assertEqual(Transaction.objects.count(), 0)

    @override_settings(PAYPAL_RECEIVER_EMAIL='merchant@example.com')
    def test_no_transaction_if_status_not_completed(self):
        ipn_mock = Mock(**{**self.valid_ipn_data, 'payment_status': 'Pending'})

        valid_ipn_received.send(sender=ipn_mock)

        self.assertEqual(Transaction.objects.count(), 0)
