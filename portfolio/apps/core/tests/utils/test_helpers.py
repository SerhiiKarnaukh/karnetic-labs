from io import StringIO
import sys

from django.test import TestCase

from accounts.models import Account
from core.utils import object_to_dict, print_object


class CoreUtilsTest(TestCase):

    def setUp(self):
        self.user = Account.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass",
            first_name="Test",
            last_name="User",
        )

    def test_object_to_dict_on_model_instance(self):
        result = object_to_dict(self.user)
        self.assertIsInstance(result, dict)
        self.assertIn("email", result)
        self.assertEqual(result["email"], "test@example.com")

    def test_object_to_dict_on_list_of_models(self):
        users = [self.user]
        result = object_to_dict(users)
        self.assertIsInstance(result, list)
        self.assertIsInstance(result[0], dict)
        self.assertEqual(result[0]["email"], "test@example.com")

    def test_print_object_output(self):
        captured_output = StringIO()
        sys.stdout = captured_output

        print_object(self.user)

        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()

        self.assertIn("test@example.com", output)
        self.assertIn("'email'", output)
