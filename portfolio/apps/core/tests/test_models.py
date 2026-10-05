
import tempfile
import os
import shutil
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import (
    Category,
    Project,
    ProjectGallery,
    ServerStatistics,
    TopbarLink,
)


@override_settings(MEDIA_ROOT=os.path.join(tempfile.gettempdir(), "media"))
class ProjectModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(title="Test Category", slug="test-category")
        self.project = Project.objects.create(
            title="Test Project",
            content="Test content",
            photo=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg"),
            github_url="https://github.com/example",
            view_url="https://example.com",
            slug="test-project",
            category=self.category,
            ordering=1,
        )

    def test_project_str_method(self):
        self.assertEqual(str(self.project), "Test Project")

    def tearDown(self):
        media_dir = os.path.join(tempfile.gettempdir(), "media")
        shutil.rmtree(media_dir, ignore_errors=True)


@override_settings(MEDIA_ROOT=os.path.join(tempfile.gettempdir(), "media"))
class ProjectGalleryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(title="Test Category", slug="test-category")
        self.project = Project.objects.create(
            title="Test Project",
            content="Test content",
            photo=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg"),
            github_url="https://github.com/example",
            view_url="https://example.com",
            slug="test-project",
            category=self.category,
            ordering=1,
        )
        self.gallery_image = ProjectGallery.objects.create(
            project=self.project,
            image=SimpleUploadedFile("gallery.jpg", b"image_data", content_type="image/jpeg"),
        )

    def test_project_gallery_str_method(self):
        self.assertEqual(str(self.gallery_image), "Test Project")

    def tearDown(self):
        media_dir = os.path.join(tempfile.gettempdir(), "media")
        shutil.rmtree(media_dir, ignore_errors=True)


class CoreModelStringTests(TestCase):
    def test_server_statistics_string_representation(self):
        statistics = ServerStatistics.objects.create(
            app_version='1.2.3',
            db_size='1 MB',
            media_size='2 MB',
            disk_total='10 MB',
            disk_used='3 MB',
            disk_available='7 MB',
        )

        self.assertIn('v1.2.3', str(statistics))

    def test_topbar_link_string_representation(self):
        link, _ = TopbarLink.objects.get_or_create(
            key=TopbarLink.Key.GITHUB,
            defaults={'title': 'GitHub', 'icon_class': 'github'},
        )

        self.assertEqual(str(link), link.title)
