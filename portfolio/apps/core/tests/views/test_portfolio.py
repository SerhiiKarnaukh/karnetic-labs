import os
import tempfile
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from core.models import Category, Project, ProjectGallery, Tag
from core.views import CategoryDetail


def get_temp_image():
    img_io = BytesIO()
    image = Image.new("RGB", (100, 100), color="blue")
    image.save(img_io, 'JPEG')
    img_io.seek(0)
    return SimpleUploadedFile("test.jpg", img_io.read(), content_type="image/jpeg")


@override_settings(MEDIA_ROOT=os.path.join(tempfile.gettempdir(), "media"))
class CoreViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(title="Vue.js", slug="vuejs")
        self.tag = Tag.objects.create(title="Web", slug="web")
        self.project = Project.objects.create(
            title="Vue Project",
            content="Awesome Vue.js project",
            photo=get_temp_image(),
            github_url="https://github.com/example/vue",
            view_url="https://example.com/vue",
            slug="vue-project",
            category=self.category,
            ordering=1
        )
        self.project.tags.add(self.tag)
        ProjectGallery.objects.create(project=self.project, image=get_temp_image())

    def test_category_detail_view(self):
        url = reverse('core:category_detail', kwargs={'slug': 'vuejs'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.project.title)
        self.assertTemplateUsed(response, 'core/index.html')

    def test_project_detail_view(self):
        url = reverse('core:project_detail', args=['vuejs', 'vue-project'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.project.title)
        self.assertTemplateUsed(response, 'core/portfolio_detail.html')

    def test_project_search_list_view(self):
        url = reverse('core:search') + '?keyword=Vue'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.project.title)
        self.assertTemplateUsed(response, 'core/index.html')

    def test_projects_by_tag_view(self):
        url = reverse('core:tag', kwargs={'slug': 'web'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.project.title)
        self.assertTemplateUsed(response, 'core/index.html')

    def tearDown(self):
        media_path = os.path.join(tempfile.gettempdir(), "media")
        if os.path.exists(media_path):
            for root, dirs, files in os.walk(media_path, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))


@override_settings(MEDIA_ROOT=os.path.join(tempfile.gettempdir(), "media"))
class CategoryDetailViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.category = Category.objects.create(
            title="Test Category",
            slug="test-category",
        )
        self.project1 = Project.objects.create(
            title="A Project",
            content="Test content",
            photo=SimpleUploadedFile(
                "test.jpg",
                b"file_content",
                content_type="image/jpeg",
            ),
            github_url="https://github.com/example",
            view_url="https://example.com",
            slug="a-project",
            category=self.category,
            ordering=1,
        )
        self.project2 = Project.objects.create(
            title="B Project",
            content="More content",
            photo=SimpleUploadedFile(
                "test2.jpg",
                b"file_content",
                content_type="image/jpeg",
            ),
            github_url="https://github.com/example2",
            view_url="https://example2.com",
            slug="b-project",
            category=self.category,
            ordering=2,
        )

    def test_default_context_without_slug_sets_welcome_title(self):
        request = self.factory.get("/fake-url/")
        view = CategoryDetail()
        view.request = request
        view.kwargs = {}
        context = view.create_store_data()
        self.assertEqual(context["core_title"], "Welcome")

    def test_queryset_without_slug_returns_all_projects_ordered(self):
        request = self.factory.get("/fake-url/")
        view = CategoryDetail()
        view.request = request
        view.kwargs = {}
        queryset = view.get_queryset()
        project_titles = list(queryset.values_list("title", flat=True))
        self.assertEqual(project_titles, ["A Project", "B Project"])

    def tearDown(self):
        import shutil

        media_dir = os.path.join(tempfile.gettempdir(), "media")
        if os.path.exists(media_dir):
            shutil.rmtree(media_dir, ignore_errors=True)
