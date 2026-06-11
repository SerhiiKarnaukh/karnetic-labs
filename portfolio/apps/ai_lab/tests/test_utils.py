import os
import tempfile
import shutil
from unittest import TestCase
from unittest.mock import patch, MagicMock
from django.test import override_settings

from ai_lab.utils import StockAPI, generate_file_name_with_extension, get_next_version_number


class StockAPITest(TestCase):

    @override_settings(ALPHA_VANTAGE_API_KEY="test_api_key")
    @patch("ai_lab.utils.stock.requests.get")
    def test_get_stock_price_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Global Quote": {
                "05. price": "150.00"
            }
        }
        mock_get.return_value = mock_response

        result = StockAPI.get_stock_price("AAPL")

        self.assertEqual(result, {"symbol": "AAPL", "price": "150.00"})
        mock_get.assert_called_once()

        params = mock_get.call_args[1]["params"]
        self.assertEqual(params["symbol"], "AAPL")
        self.assertEqual(params["apikey"], "test_api_key")
        self.assertEqual(params["function"], "GLOBAL_QUOTE")

    @override_settings(ALPHA_VANTAGE_API_KEY=None)
    def test_missing_api_key_raises_value_error(self):
        with self.assertRaises(ValueError) as context:
            StockAPI.get_stock_price("AAPL")
        self.assertIn("Missing API key", str(context.exception))

    @override_settings(ALPHA_VANTAGE_API_KEY="test_api_key")
    @patch("ai_lab.utils.stock.requests.get")
    def test_non_200_response_raises_connection_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_get.return_value = mock_response

        with self.assertRaises(ConnectionError) as context:
            StockAPI.get_stock_price("AAPL")
        self.assertIn("API error: 503", str(context.exception))


class FileNameGenerationTest(TestCase):
    def setUp(self):
        self.test_dir = os.path.join(tempfile.gettempdir(), "test_ai_utils")
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_generate_filename_initial_version(self):
        prompt = "Generate a 3D Model"
        filename = generate_file_name_with_extension(prompt, self.test_dir, "png")
        self.assertTrue(filename.startswith("generate_a_3d_model_v1."))
        self.assertTrue(filename.endswith(".png"))

    def test_generate_filename_increments_version(self):
        # Create dummy files for existing versions
        base = "generate_a_3d_model"
        open(os.path.join(self.test_dir, f"{base}_v1.png"), "a").close()
        open(os.path.join(self.test_dir, f"{base}_v2.png"), "a").close()

        prompt = "Generate a 3D Model"
        filename = generate_file_name_with_extension(prompt, self.test_dir, "png")
        self.assertEqual(filename, f"{base}_v3.png")

    def test_get_next_version_when_directory_missing(self):
        # simulate missing directory
        nonexistent_dir = os.path.join(tempfile.gettempdir(), "nonexistent_subdir")
        version = get_next_version_number("anything", "png", nonexistent_dir)
        self.assertEqual(version, 1)

    def test_get_next_version_skips_irrelevant_files(self):
        base = "generate_a_3d_model"
        # add unrelated files
        open(os.path.join(self.test_dir, f"{base}_v1.txt"), "a").close()
        open(os.path.join(self.test_dir, f"{base}_v5.png"), "a").close()

        version = get_next_version_number(base, "png", self.test_dir)
        self.assertEqual(version, 6)
