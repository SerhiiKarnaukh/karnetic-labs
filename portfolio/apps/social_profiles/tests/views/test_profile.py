import os
import shutil
import tempfile

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from core.utils import create_active_user, create_test_image
from social_profiles.models import Profile


@override_settings(
    MEDIA_ROOT=os.path.join(tempfile.gettempdir(), 'social_profiles_profile_media')
)
class ProfileViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_active_user(
            email='profile@example.com',
            username='profile',
            password='testpass123',
            first_name='Profile',
            last_name='User',
        )
        self.profile = Profile.objects.create(user=self.user)
        self.client.force_authenticate(self.user)

    def tearDown(self):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def test_me_returns_profile(self):
        response = self.client.get(reverse('social_profiles:me'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'profile')

    def test_me_returns_404_without_profile(self):
        user = create_active_user(
            email='missing@example.com',
            username='missing',
            password='testpass123',
            first_name='Missing',
            last_name='Profile',
        )
        self.client.force_authenticate(user)

        response = self.client.get(reverse('social_profiles:me'))

        self.assertEqual(response.status_code, 404)

    def test_edit_profile_updates_avatar_and_account(self):
        response = self.client.post(
            reverse('social_profiles:editprofile'),
            {
                'email': 'updated@example.com',
                'username': 'updated',
                'first_name': 'Updated',
                'last_name': 'Name',
                'avatar': create_test_image('avatar.png'),
            },
            format='multipart',
        )

        self.assertEqual(response.json()['message'], 'Information updated successfully')
        self.profile.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(self.profile.username, 'updated')
        self.assertEqual(self.user.email, 'updated@example.com')
        self.assertIn('/social/avatars/', response.json()['new_avatar'])

    def test_edit_profile_rejects_duplicate_email(self):
        other = create_active_user(
            email='taken@example.com',
            username='taken',
            password='testpass123',
            first_name='Taken',
            last_name='User',
        )
        Profile.objects.create(user=other)

        response = self.client.post(
            reverse('social_profiles:editprofile'),
            {'email': 'taken@example.com', 'username': 'profile'},
        )

        self.assertEqual(response.json()['message'], 'Email already exists!')

    def test_edit_profile_rejects_duplicate_username(self):
        other = create_active_user(
            email='other@example.com',
            username='taken',
            password='testpass123',
            first_name='Taken',
            last_name='User',
        )
        Profile.objects.create(user=other)

        response = self.client.post(
            reverse('social_profiles:editprofile'),
            {'email': 'profile@example.com', 'username': 'taken'},
        )

        self.assertEqual(response.json()['message'], 'Username already exists!')

    def test_edit_profile_rejects_invalid_form(self):
        response = self.client.post(
            reverse('social_profiles:editprofile'),
            {'email': 'profile@example.com', 'username': ''},
        )

        self.assertEqual(response.json()['message'], 'Invalid form data!')

    def test_edit_profile_without_profile_raises_attribute_error(self):
        user = create_active_user(
            email='orphan@example.com',
            username='orphan',
            password='testpass123',
            first_name='Orphan',
            last_name='User',
        )
        self.client.force_authenticate(user)

        with self.assertRaises(AttributeError):
            self.client.post(
                reverse('social_profiles:editprofile'),
                {'email': 'orphan@example.com', 'username': 'orphan'},
            )

    def test_edit_password_changes_password(self):
        response = self.client.post(
            reverse('social_profiles:editpassword'),
            {
                'old_password': 'testpass123',
                'new_password1': 'new-testpass123',
                'new_password2': 'new-testpass123',
            },
        )

        self.assertEqual(response.json()['message'], 'success')
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('new-testpass123'))

    def test_edit_password_returns_form_errors(self):
        response = self.client.post(
            reverse('social_profiles:editpassword'),
            {'old_password': 'incorrect'},
        )

        self.assertIn('old_password', response.json()['message'])
