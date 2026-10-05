from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

class ProfileApiOrdersTest(TestCase):
    def test_requires_authentication(self):
        self.assertEqual(APIClient().get(reverse("taberna-api-user-orders")).status_code, 401)

    def test_returns_authenticated_orders(self):
        from core.utils import create_active_user
        from taberna_profiles.models import UserProfile
        user = create_active_user(email="orders-api@example.com", username="orders-api", password="pass123", first_name="Orders", last_name="Api")
        UserProfile.objects.create(user=user)
        client = APIClient()
        client.force_authenticate(user)
        self.assertEqual(client.get(reverse("taberna-api-user-orders")).status_code, 200)
