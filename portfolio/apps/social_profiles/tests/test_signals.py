import os
import shutil
import tempfile
import uuid

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from core.utils import create_active_user
from social_profiles.models import Profile
from social_profiles.signals.profile import delete_old_avatar


@override_settings(MEDIA_ROOT=os.path.join(tempfile.gettempdir(), 'social_profiles_signal_media'))
class ProfileSignalTests(TestCase):
    def setUp(self):
        user = create_active_user(
            email='signal@example.com',
            username='signal',
            password='testpass123',
            first_name='Signal',
            last_name='User',
        )
        self.profile = Profile.objects.create(
            user=user,
            avatar=SimpleUploadedFile('old.png', b'old', content_type='image/png'),
        )

    def tearDown(self):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def test_replacing_avatar_deletes_previous_file(self):
        old_path = self.profile.avatar.path
        self.profile.avatar = SimpleUploadedFile(
            'new.png', b'new', content_type='image/png'
        )
        self.profile.save()

        self.assertFalse(os.path.exists(old_path))
        self.assertTrue(os.path.exists(self.profile.avatar.path))

    def test_ignores_profile_that_no_longer_exists(self):
        missing = Profile(user=self.profile.user)
        missing.pk = uuid.uuid4()

        delete_old_avatar(Profile, missing)
