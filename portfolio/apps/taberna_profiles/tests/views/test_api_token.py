from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from core.utils import create_active_user
from taberna_profiles.models import UserProfile


class ProfileApiTokenTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("token_obtain_pair")

    def test_obtains_token(self):
        user = create_active_user(
            email="token@example.com",
            username="token",
            password="pass123",
            first_name="Token",
            last_name="User",
        )
        UserProfile.objects.create(user=user)

        response = self.client.post(
            self.url, {"email": user.email, "password": "pass123"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)

    def test_missing_profile_returns_400(self):
        user = create_active_user(
            email="noprofile-token@example.com",
            username="noprofile-token",
            password="pass123",
            first_name="No",
            last_name="Profile",
        )

        response = self.client.post(
            self.url, {"email": user.email, "password": "pass123"}
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "User profile does not exist.")

    @patch(
        "taberna_profiles.views.api.token.handle_cart_after_login",
        side_effect=Exception("cart failed"),
    )
    def test_cart_exception_returns_400(self, _):
        user = create_active_user(
            email="cart-error@example.com",
            username="cart-error",
            password="pass123",
            first_name="Cart",
            last_name="Error",
        )
        UserProfile.objects.create(user=user)

        response = self.client.post(
            self.url, {"email": user.email, "password": "pass123"}
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("An error occurred", response.data["error"])

    @patch("taberna_profiles.views.api.token.authenticate", return_value=None)
    def test_invalid_credentials_after_valid_serializer(self, _):
        user = create_active_user(
            email="auth-none@example.com",
            username="auth-none",
            password="pass123",
            first_name="Auth",
            last_name="None",
        )
        UserProfile.objects.create(user=user)

        response = self.client.post(
            self.url, {"email": user.email, "password": "pass123"}
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["error"], "Invalid login credentials.")

    def test_invalid_payload_returns_authentication_failed(self):
        response = self.client.post(self.url, {"email": "bad"}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("Authentication failed", response.data["error"])
