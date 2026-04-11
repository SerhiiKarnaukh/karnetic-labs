import os
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from social_profiles.models import Profile

User = get_user_model()


def _avatar_file():
    return SimpleUploadedFile('a.gif', b'GIF89a', content_type='image/gif')


@override_settings(
    MEDIA_ROOT=os.path.join(tempfile.gettempdir(), 'test_social_profiles_media'),
)
class SocialTokenObtainPairViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('social_profiles:social-token-obtain-pair')

    def _create_active_user(self, **kwargs):
        defaults = {
            'email': 'soc@example.com',
            'username': 'socuser',
            'password': 'testpass123',
            'first_name': 'S',
            'last_name': 'O',
        }
        defaults.update(kwargs)
        password = defaults.pop('password')
        user = User.objects.create_user(password=password, **defaults)
        user.is_active = True
        user.save(update_fields=['is_active'])
        return user

    def test_no_profile_returns_400(self):
        self._create_active_user()
        res = self.client.post(
            self.url,
            {'email': 'soc@example.com', 'password': 'testpass123'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data.get('error'), 'User profile does not exist.')

    def test_with_profile_returns_tokens(self):
        user = self._create_active_user()
        Profile.objects.create(
            user=user,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
            email=user.email,
            avatar=_avatar_file(),
        )
        res = self.client.post(
            self.url,
            {'email': 'soc@example.com', 'password': 'testpass123'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)
