from django.test import TestCase

from social_profiles.utils import get_random_code


class RandomCodeTests(TestCase):
    def test_returns_eight_lowercase_characters(self):
        code = get_random_code()

        self.assertEqual(len(code), 8)
        self.assertTrue(code.islower())
