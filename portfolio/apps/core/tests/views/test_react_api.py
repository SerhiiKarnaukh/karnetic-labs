import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import Category, Project


def _photo(name):
    return SimpleUploadedFile(name, b'file_content', content_type='image/jpeg')


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class CoreReactApiTest(TestCase):
    def setUp(self):
        self.react_category = Category.objects.create(
            title='React',
            slug='react',
        )
        self.vue_category = Category.objects.create(
            title='Vue.js',
            slug='vuejs',
        )
        self.project1 = Project.objects.create(
            title='React Project 1',
            content='This is a React project',
            category=self.react_category,
            github_url='https://github.com/example/react-1',
            view_url='/project-1/',
            photo=_photo('photo.jpg'),
            slug='react-project',
        )
        self.project2 = Project.objects.create(
            title='Another React Project',
            content='Hooks and components demo',
            category=self.react_category,
            github_url='https://github.com/example/react-2',
            view_url='/project-2/',
            photo=_photo('photo2.jpg'),
            slug='react-project-2',
        )
        self.vue_project = Project.objects.create(
            title='Vue Project',
            content='Should not appear in React API',
            category=self.vue_category,
            github_url='https://github.com/example/vue',
            view_url='/vue/',
            photo=_photo('vue.jpg'),
            slug='vue-project',
        )

    def test_react_apps_api_list_returns_react_projects(self):
        url = reverse('core:react_apps_api')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        titles = {item['title'] for item in response.data}
        self.assertEqual(titles, {'React Project 1', 'Another React Project'})

    def test_react_apps_api_list_excludes_other_categories(self):
        url = reverse('core:react_apps_api')
        response = self.client.get(url)

        titles = [item['title'] for item in response.data]
        self.assertNotIn('Vue Project', titles)

    def test_react_apps_api_list_returns_empty_when_no_react_projects(self):
        Project.objects.filter(category=self.react_category).delete()
        url = reverse('core:react_apps_api')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_react_apps_api_list_response_fields(self):
        url = reverse('core:react_apps_api')
        response = self.client.get(url)
        item = next(
            project for project in response.data
            if project['title'] == 'React Project 1'
        )

        self.assertEqual(
            set(item.keys()),
            {'id', 'title', 'photo', 'github_url', 'view_url', 'url'},
        )
        self.assertEqual(item['id'], self.project1.id)
        self.assertEqual(item['github_url'], self.project1.github_url)
        self.assertEqual(item['view_url'], self.project1.view_url)
        self.assertTrue(item['photo'])
        self.assertIn('/category/react/react-project/', item['url'])

    def test_react_apps_api_list_builds_absolute_url(self):
        url = reverse('core:react_apps_api')
        response = self.client.get(url)
        item = response.data[0]

        self.assertTrue(item['url'].startswith('http'))

    def test_react_apps_api_list_rejects_post(self):
        url = reverse('core:react_apps_api')
        response = self.client.post(url, {}, content_type='application/json')

        self.assertEqual(response.status_code, 405)

    def test_react_search_api_returns_filtered_by_title(self):
        url = reverse('core:react_search_api')
        response = self.client.post(
            url,
            {'query': 'Another'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Another React Project')

    def test_react_search_api_returns_filtered_by_content(self):
        url = reverse('core:react_search_api')
        response = self.client.post(
            url,
            {'query': 'Hooks'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Another React Project')

    def test_react_search_api_is_case_insensitive(self):
        url = reverse('core:react_search_api')
        response = self.client.post(
            url,
            {'query': 'hooks'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Another React Project')

    def test_react_search_api_excludes_other_categories(self):
        url = reverse('core:react_search_api')
        response = self.client.post(
            url,
            {'query': 'Vue'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_react_search_api_returns_absolute_photo_and_url(self):
        url = reverse('core:react_search_api')
        response = self.client.post(
            url,
            {'query': 'Another'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data[0]['photo'].startswith('http'))
        self.assertTrue(response.data[0]['url'].startswith('http'))

    def test_react_search_api_empty_query_returns_empty_list(self):
        url = reverse('core:react_search_api')
        response = self.client.post(
            url,
            {'query': ''},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('projects', response.data)
        self.assertEqual(response.data['projects'], [])

    def test_react_search_api_missing_query_returns_empty_list(self):
        url = reverse('core:react_search_api')
        response = self.client.post(url, {}, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'projects': []})

    def test_react_search_api_no_matches_returns_empty_array(self):
        url = reverse('core:react_search_api')
        response = self.client.post(
            url,
            {'query': 'nonexistent-term-xyz'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_react_search_api_rejects_get(self):
        url = reverse('core:react_search_api')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 405)

    def test_react_search_api_response_fields(self):
        url = reverse('core:react_search_api')
        response = self.client.post(
            url,
            {'query': 'React Project 1'},
            content_type='application/json',
        )
        item = response.data[0]

        self.assertEqual(
            set(item.keys()),
            {'id', 'title', 'photo', 'github_url', 'view_url', 'url'},
        )
        self.assertEqual(item['id'], self.project1.id)
        self.assertEqual(item['github_url'], self.project1.github_url)
        self.assertEqual(item['view_url'], self.project1.view_url)
