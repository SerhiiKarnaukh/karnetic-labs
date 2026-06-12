import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import Category, Project


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class CoreAngularApiTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(title="Angular", slug="angular")
        self.project1 = Project.objects.create(
            title="Angular Project 1",
            content="This is an Angular project",
            category=self.category,
            view_url="/project-1/",
            photo=SimpleUploadedFile(
                "photo.jpg",
                b"file_content",
                content_type="image/jpeg",
            ),
            slug="angular-project",
        )
        self.project2 = Project.objects.create(
            title="Another Angular Project",
            content="Another Angular content",
            category=self.category,
            view_url="/project-2/",
            photo=SimpleUploadedFile(
                "photo2.jpg",
                b"file_content",
                content_type="image/jpeg",
            ),
            slug="angular-project-2",
        )

    def test_angular_apps_api_list_returns_angular_projects(self):
        url = reverse("core:angular_apps_api")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_angular_search_api_returns_filtered_projects(self):
        url = reverse("core:angular_search_api")
        response = self.client.post(
            url,
            {"query": "Another"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertIn("Another Angular Project", response.data[0]["title"])
        self.assertTrue(response.data[0]["photo"].startswith("http"))
        self.assertTrue(response.data[0]["url"].startswith("http"))

    def test_angular_search_api_empty_query_returns_empty_list(self):
        url = reverse("core:angular_search_api")
        response = self.client.post(
            url,
            {"query": ""},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("projects", response.data)
        self.assertEqual(response.data["projects"], [])
