from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from core.utils import create_active_user
from social_profiles.models import Profile


class SocialProfileCreateViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('social_profiles:user-register')
        self.data = {
            'email': 'new@example.com',
            'username': 'newuser',
            'password': 'testpass123',
            'first_name': 'New',
            'last_name': 'User',
        }

    @patch('social_profiles.views.registration.send_activation_email')
    def test_registration_creates_profile_and_sends_activation(self, mock_email):
        response = self.client.post(self.url, self.data, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Profile.objects.filter(username='newuser').exists())
        mock_email.assert_called_once()

    @patch('social_profiles.views.registration.send_activation_email')
    def test_duplicate_account_without_profile_creates_missing_profile(self, mock_email):
        user = create_active_user(
            email=self.data['email'],
            username=self.data['username'],
            password=self.data['password'],
            first_name='New',
            last_name='User',
        )

        response = self.client.post(self.url, self.data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['detail'], 'social_profile_created')
        self.assertTrue(Profile.objects.filter(user=user).exists())
        mock_email.assert_not_called()

    def test_invalid_registration_returns_validation_error(self):
        response = self.client.post(self.url, {'email': 'invalid@example.com'}, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('password', response.data)

    @patch(
        'rest_framework.generics.CreateAPIView.create',
        side_effect=Exception('temporary failure'),
    )
    def test_non_unique_exception_returns_400_with_valid_data(self, _):
        response = self.client.post(self.url, self.data, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['email'], self.data['email'])
