from django.test import TestCase
from django.urls import reverse

from core.models import TopbarLink
from core.utils.topbar_links import get_active_topbar_links


class TopbarLinkModelTest(TestCase):
    def setUp(self):
        TopbarLink.objects.all().delete()
        TopbarLink.objects.create(
            key=TopbarLink.Key.CV,
            url='https://example.com/cv',
            title='CV',
            icon_class='fas fa-user-cog',
            ordering=0,
        )
        TopbarLink.objects.create(
            key=TopbarLink.Key.GITHUB,
            url='',
            title='GitHub Account',
            icon_class='fab fa-github fw-normal',
            ordering=1,
        )
        TopbarLink.objects.create(
            key=TopbarLink.Key.LINKEDIN,
            url='https://example.com/linkedin',
            title='LinkedIn Account',
            icon_class='fab fa-linkedin-in fw-normal',
            ordering=2,
        )

    def test_get_active_topbar_links_excludes_empty_urls(self):
        links = list(get_active_topbar_links())

        self.assertEqual(len(links), 2)
        self.assertEqual(links[0].key, TopbarLink.Key.CV)
        self.assertEqual(links[1].key, TopbarLink.Key.LINKEDIN)


class TopbarLinksApiTest(TestCase):
    def setUp(self):
        TopbarLink.objects.all().delete()
        TopbarLink.objects.create(
            key=TopbarLink.Key.CV,
            url='https://example.com/cv',
            title='CV',
            icon_class='fas fa-user-cog',
            ordering=0,
        )
        TopbarLink.objects.create(
            key=TopbarLink.Key.GITHUB,
            url='',
            title='GitHub Account',
            icon_class='fab fa-github fw-normal',
            ordering=1,
        )

    def test_topbar_links_api_returns_only_non_empty_links(self):
        url = reverse('core:topbar_links_api')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['key'], 'cv')
        self.assertEqual(response.data[0]['url'], 'https://example.com/cv')
        self.assertEqual(response.data[0]['title'], 'CV')
        self.assertEqual(response.data[0]['icon_class'], 'fas fa-user-cog')
