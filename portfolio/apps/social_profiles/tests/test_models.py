from unittest.mock import patch

from django.test import TestCase

from core.utils import create_active_user
from social_profiles.models import Profile


class ProfileModelTests(TestCase):
    def create_user(self, username, first_name='First', last_name='Last'):
        return create_active_user(
            email=f'{username}@example.com',
            username=username,
            password='testpass123',
            first_name=first_name,
            last_name=last_name,
        )

    def test_defaults_fields_slug_and_string_from_account(self):
        user = self.create_user('account')

        profile = Profile.objects.create(user=user)

        self.assertEqual(profile.full_name(), 'First Last')
        self.assertEqual(profile.slug, 'first-last')
        self.assertIn('account-', str(profile))

    def test_updates_related_account_fields(self):
        profile = Profile.objects.create(user=self.create_user('before'))
        profile.first_name = 'After'
        profile.last_name = 'Update'
        profile.email = 'after@example.com'
        profile.username = 'after'
        profile.save()

        profile.user.refresh_from_db()
        self.assertEqual(profile.user.first_name, 'After')
        self.assertEqual(profile.user.last_name, 'Update')
        self.assertEqual(profile.user.email, 'after@example.com')
        self.assertEqual(profile.user.username, 'after')
        self.assertEqual(profile.slug, 'after-update')

    @patch('social_profiles.models.profile.get_random_code', return_value='unique')
    def test_appends_random_code_when_slug_exists(self, mock_random_code):
        Profile.objects.create(user=self.create_user('first'))

        profile = Profile.objects.create(user=self.create_user('second'))

        self.assertEqual(profile.slug, 'first-last-unique')
        mock_random_code.assert_called_once()

    def test_uses_username_slug_when_account_has_no_names(self):
        user = self.create_user('nameless', first_name='', last_name='')

        profile = Profile.objects.create(user=user)

        self.assertEqual(profile.slug, 'nameless')
