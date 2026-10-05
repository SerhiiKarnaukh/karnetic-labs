from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from core.utils import create_active_user
from taberna_profiles.models import UserProfile


class ProfileApiAuthTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("taberna-api-register")
        self.data = {
            "email": "api-register@example.com",
            "username": "api-register",
            "password": "pass123",
            "first_name": "Api",
            "last_name": "User",
        }

    @patch("taberna_profiles.views.api.auth.send_activation_email")
    def test_creates_profile(self, mock_email):
        response = self.client.post(self.url, self.data, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            UserProfile.objects.filter(user__email=self.data["email"]).exists()
        )
        mock_email.assert_called_once()

    def test_duplicate_account_without_profile_creates_missing_profile(self):
        user = create_active_user(
            email=self.data["email"],
            username=self.data["username"],
            password=self.data["password"],
            first_name="Api",
            last_name="User",
        )

        response = self.client.post(self.url, self.data, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["detail"], "taberna_profile_created")
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    @patch(
        "rest_framework.generics.CreateAPIView.create",
        side_effect=Exception("temporary failure"),
    )
    def test_non_unique_exception_returns_400_with_valid_data(self, _):
        response = self.client.post(self.url, self.data, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["email"], self.data["email"])
