from django.test import TestCase
from taberna_profiles.forms import RegistrationForm


class ProfileFormsTest(TestCase):
    def test_rejects_mismatched_passwords(self):
        form = RegistrationForm(
            {
                "first_name": "A",
                "last_name": "B",
                "phone_number": "1",
                "email": "form@example.com",
                "password": "one",
                "confirm_password": "two",
            }
        )
        self.assertFalse(form.is_valid())

    def test_rejects_existing_profile_email(self):
        from core.utils import create_active_user
        from taberna_profiles.models import UserProfile
        user = create_active_user(
            email="existing@example.com",
            username="existing",
            password="pass123",
            first_name="Existing",
            last_name="User",
        )
        UserProfile.objects.create(user=user)
        form = RegistrationForm(
            {
                "first_name": "A",
                "last_name": "B",
                "phone_number": "1",
                "email": user.email,
                "password": "pass123",
                "confirm_password": "pass123",
            }
        )
        self.assertFalse(form.is_valid())
