from django.test import TestCase, RequestFactory
from unittest.mock import patch, MagicMock
from accounts.models import Account
from accounts.utils import send_activation_email


class SendActivationEmailWithRequestTest(TestCase):

    def setUp(self):
        self.user = Account.objects.create_user(
            email="activate@example.com",
            username="activator",
            password="Activate123",
            first_name="Activate",
            last_name="User"
        )
        self.factory = RequestFactory()
        self.request = self.factory.get("/")

    @patch("accounts.utils.emails.get_current_site")
    @patch("accounts.utils.emails.EmailMessage")
    def test_email_sent_with_request_context(self, mock_email_class, mock_get_current_site):
        mock_get_current_site.return_value.domain = "mockedsite.com"

        mock_email = MagicMock()
        mock_email_class.return_value = mock_email

        send_activation_email(self.user, self.request)

        mock_email_class.assert_called_once()
        subject = mock_email_class.call_args[0][0]
        to = mock_email_class.call_args[1]["to"]

        self.assertIn("Please activate your account", subject)
        self.assertEqual(to, [self.user.email])

        mock_email.send.assert_called_once()
