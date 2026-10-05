from django.test import TestCase
from core.utils import create_active_user
from taberna_profiles.models import UserProfile

class ProfileModelsTest(TestCase):
    def test_profile_helpers(self):
        user = create_active_user(email="profile@example.com", username="profile", password="pass123", first_name="Profile", last_name="User")
        profile = UserProfile.objects.create(user=user, address_line_1="Street", address_line_2="Suite")
        self.assertEqual(str(profile), "Profile User")
        self.assertEqual(profile.full_address(), "Street Suite")
