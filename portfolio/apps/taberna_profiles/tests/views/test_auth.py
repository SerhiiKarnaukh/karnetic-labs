from unittest.mock import patch

from django.contrib.auth.tokens import default_token_generator
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from core.utils import create_active_user
from taberna_profiles.models import UserProfile


class AuthViewsTest(TestCase):
    def test_register_get_renders_form(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "taberna_profiles/register.html")

    def test_register_existing_account_without_profile_creates_profile(self):
        user = create_active_user(
            email="existing@example.com",
            username="existing",
            password="pass123",
            first_name="Existing",
            last_name="User",
        )

        response = self.client.post(
            reverse("register"),
            {
                "first_name": "Existing",
                "last_name": "User",
                "phone_number": "1",
                "email": user.email,
                "password": "pass123",
                "confirm_password": "pass123",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("login"))
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    @patch("taberna_profiles.views.auth.send_activation_email")
    def test_register_login_logout_and_password_pages(self, _):
        response = self.client.post(
            reverse("register"),
            {
                "first_name": "New",
                "last_name": "User",
                "phone_number": "1",
                "email": "new@example.com",
                "password": "pass123",
                "confirm_password": "pass123",
            },
        )
        self.assertEqual(response.status_code, 302)

        user = create_active_user(
            email="auth@example.com",
            username="auth",
            password="pass123",
            first_name="Auth",
            last_name="User",
        )
        UserProfile.objects.create(user=user)
        self.assertEqual(
            self.client.post(
                reverse("login"), {"email": user.email, "password": "pass123"}
            ).status_code,
            302,
        )
        self.assertEqual(self.client.get(reverse("logout")).status_code, 302)
        self.assertEqual(self.client.get(reverse("forgotPassword")).status_code, 200)
        self.assertEqual(self.client.get(reverse("resetPassword")).status_code, 200)
        self.assertEqual(self.client.get(reverse("activate_result")).status_code, 200)

    def test_login_get_renders_page(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "taberna_profiles/login.html")

    def test_login_missing_profile_redirects(self):
        user = create_active_user(
            email="noprofile@example.com",
            username="noprofile",
            password="pass123",
            first_name="No",
            last_name="Profile",
        )

        response = self.client.post(
            reverse("login"), {"email": user.email, "password": "pass123"}
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("login"))

    @patch(
        "taberna_profiles.views.auth.handle_cart_after_login",
        side_effect=Exception("cart failed"),
    )
    def test_login_handles_unexpected_exception(self, _):
        user = create_active_user(
            email="error@example.com",
            username="error",
            password="pass123",
            first_name="Error",
            last_name="User",
        )
        UserProfile.objects.create(user=user)

        response = self.client.post(
            reverse("login"), {"email": user.email, "password": "pass123"}
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("login"))

    def test_login_invalid_credentials_redirects(self):
        response = self.client.post(
            reverse("login"),
            {"email": "missing@example.com", "password": "wrong"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("login"))

    def test_activation_password_reset_and_change_password_branches(self):
        user = create_active_user(
            email="branches@example.com",
            username="branches",
            password="pass123",
            first_name="Branch",
            last_name="User",
        )
        UserProfile.objects.create(user=user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        self.assertEqual(
            self.client.get(reverse("activate", args=[uid, token])).status_code, 302
        )
        self.assertEqual(
            self.client.get(reverse("activate", args=[uid, "bad"])).status_code, 302
        )
        self.assertEqual(
            self.client.get(reverse("activate", args=["bad-uid", token])).status_code,
            302,
        )

        with patch("taberna_profiles.views.auth.EmailMessage.send"):
            self.assertEqual(
                self.client.post(
                    reverse("forgotPassword"), {"email": user.email}
                ).status_code,
                302,
            )
        self.assertEqual(
            self.client.post(
                reverse("forgotPassword"), {"email": "missing@example.com"}
            ).status_code,
            302,
        )

        self.assertEqual(
            self.client.get(
                reverse("resetpassword_validate", args=[uid, token])
            ).status_code,
            302,
        )
        self.assertEqual(
            self.client.get(
                reverse("resetpassword_validate", args=[uid, "bad"])
            ).status_code,
            302,
        )
        self.assertEqual(
            self.client.get(
                reverse("resetpassword_validate", args=["bad-uid", token])
            ).status_code,
            302,
        )

        session = self.client.session
        session["uid"] = str(user.pk)
        session.save()
        self.assertEqual(
            self.client.post(
                reverse("resetPassword"),
                {"password": "newpass123", "confirm_password": "newpass123"},
            ).status_code,
            302,
        )
        user.refresh_from_db()
        self.assertTrue(user.check_password("newpass123"))

        session = self.client.session
        session["uid"] = str(user.pk)
        session.save()
        self.assertEqual(
            self.client.post(
                reverse("resetPassword"),
                {"password": "a", "confirm_password": "b"},
            ).status_code,
            302,
        )

        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("change_password")).status_code, 200)
        self.assertEqual(
            self.client.post(
                reverse("change_password"),
                {
                    "current_password": "wrong",
                    "new_password": "x",
                    "confirm_password": "x",
                },
            ).status_code,
            302,
        )
        self.assertEqual(
            self.client.post(
                reverse("change_password"),
                {
                    "current_password": "newpass123",
                    "new_password": "a",
                    "confirm_password": "b",
                },
            ).status_code,
            302,
        )
        self.assertEqual(
            self.client.post(
                reverse("change_password"),
                {
                    "current_password": "newpass123",
                    "new_password": "newerpass",
                    "confirm_password": "newerpass",
                },
            ).status_code,
            302,
        )
