import os
import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase, override_settings

from core.utils import create_active_user
from social_profiles.models import Profile
from social_profiles.serializers import ProfileSerializer


@override_settings(MEDIA_ROOT=os.path.join(tempfile.gettempdir(), 'social_profiles_serializer_media'))
class ProfileSerializerTests(TestCase):
    def setUp(self):
        user = create_active_user(
            email='serializer@example.com',
            username='serializer',
            password='testpass123',
            first_name='Serializer',
            last_name='User',
        )
        self.profile = Profile.objects.create(user=user)

    def tearDown(self):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def test_returns_none_avatar_url_without_request(self):
        self.assertIsNone(ProfileSerializer(self.profile).data['avatar_url'])

    def test_builds_absolute_avatar_url_with_request(self):
        self.profile.avatar = SimpleUploadedFile(
            'avatar.png', b'image', content_type='image/png'
        )
        self.profile.save()
        request = RequestFactory().get('/')

        data = ProfileSerializer(self.profile, context={'request': request}).data

        self.assertEqual(data['full_name'], 'Serializer User')
        self.assertIn(
            f'http://testserver{settings.MEDIA_URL}social/avatars/',
            data['avatar_url'],
        )
