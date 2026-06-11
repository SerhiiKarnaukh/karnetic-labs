from django.test import TestCase,  override_settings
from unittest.mock import patch, MagicMock
from django.urls import reverse
from django.conf import settings
import tempfile
import os

from base64 import b64encode
from core.utils import create_test_image


class AiLabChatViewTest(TestCase):
    @patch("ai_lab.views.chat.OpenAIService")
    def test_text_only_request_success(self, mock_service_class):
        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.type = "text"
        mock_response.content = [MagicMock(text="Funny AI joke")]
        mock_service.get_ai_response.return_value = mock_response
        mock_service_class.return_value = mock_service

        response = self.client.post(reverse("ai_lab:ai_lab_api"), {
            "question": "Tell me a joke."
        }, content_type="application/json")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Funny AI joke", response.data["message"])

    @patch("ai_lab.views.chat.OpenAIService")
    @patch("ai_lab.views.chat.StockAPI.get_stock_price")
    def test_function_call_and_follow_up_success(self, mock_stock, mock_service_class):
        mock_service = MagicMock()
        function_call_response = MagicMock()
        function_call_response.type = "function_call"
        function_call_response.name = "get_stock_price"
        function_call_response.arguments = '{"symbol": "AAPL"}'
        function_call_response.call_id = "abc123"

        follow_up_response = MagicMock()
        follow_up_response.type = "text"
        follow_up_response.content = [MagicMock(text="Stock joke")]

        mock_service.get_ai_response.side_effect = [
            function_call_response, follow_up_response
        ]
        mock_service_class.return_value = mock_service
        mock_stock.return_value = {"price": 123}

        response = self.client.post(reverse("ai_lab:ai_lab_api"), {
            "question": "What is AAPL price?"
        }, content_type="application/json")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Stock joke", response.data["message"])

    @patch("ai_lab.views.chat.OpenAIService")
    def test_service_error_returns_500(self, mock_service_class):
        mock_service = MagicMock()
        mock_service.get_ai_response.side_effect = Exception("OpenAI down")
        mock_service_class.return_value = mock_service

        response = self.client.post(reverse("ai_lab:ai_lab_api"), {
            "question": "Something"
        }, content_type="application/json")

        self.assertEqual(response.status_code, 500)
        self.assertIn("OpenAI down", response.data["message"])

    @patch("ai_lab.views.chat.OpenAIService")
    def test_image_prompt_included_in_user_content(self, mock_service_class):
        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.type = "text"
        mock_response.content = [MagicMock(text="Image-based joke")]
        mock_service.get_ai_response.return_value = mock_response
        mock_service_class.return_value = mock_service

        image_urls = ["http://example.com/image1.png", "http://example.com/image2.png"]

        response = self.client.post(reverse("ai_lab:ai_lab_api"), {
            "question": "Make a joke about these images.",
            "prompt_images": image_urls
        }, content_type="application/json")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Image-based joke", response.data["message"])

        call_args = mock_service.get_ai_response.call_args[0][0]  # messages list
        user_msg = call_args[1]  # {"role": "user", "content": [...]}
        content_list = user_msg["content"]

        self.assertIn({"type": "input_text", "text": "Make a joke about these images."}, content_list)
        self.assertIn({
            "type": "input_image",
            "image_url": "http://example.com/image1.png",
            "detail": "low"
        }, content_list)
        self.assertIn({
            "type": "input_image",
            "image_url": "http://example.com/image2.png",
            "detail": "low"
        }, content_list)


@override_settings(MEDIA_ROOT=os.path.join(tempfile.gettempdir(), "media"))
class AiLabImageGeneratorViewTest(TestCase):

    def setUp(self):
        self.url = reverse("ai_lab:ai_lab_image_generator")
        self.prompt = "A robot eating ice cream"
        self.test_filename = "robot.png"
        self.generated_images_dir = os.path.join(settings.MEDIA_ROOT, "generated_images")
        self.test_file_path = os.path.join(self.generated_images_dir, self.test_filename)

    def tearDown(self):
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)
        if os.path.exists(self.generated_images_dir) and not os.listdir(self.generated_images_dir):
            os.rmdir(self.generated_images_dir)
        if os.path.exists(settings.MEDIA_ROOT) and not os.listdir(settings.MEDIA_ROOT):
            os.rmdir(settings.MEDIA_ROOT)

    @patch("ai_lab.views.image.OpenAIService")
    @patch("ai_lab.views.image.requests.get")
    @patch("ai_lab.views.image.generate_file_name_with_extension", return_value="robot.png")
    def test_image_generated_and_saved_successfully(self, mock_filename, mock_requests_get, mock_openai_service):
        mock_service = MagicMock()
        mock_service.get_img_gen_response.return_value = "http://mocked.image.url/image.png"
        mock_openai_service.return_value = mock_service

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "image/png"}
        mock_response.iter_content = lambda chunk_size: [b"imagebytes"]
        mock_requests_get.return_value = mock_response

        response = self.client.post(self.url, {"question": self.prompt}, content_type="application/json")

        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.data)
        self.assertIn("generated_images/robot.png", response.data["message"])
        self.assertTrue(os.path.exists(self.test_file_path))

    def test_missing_prompt_returns_400(self):
        response = self.client.post(self.url, {}, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "Prompt is required.")

    @patch("ai_lab.views.image.OpenAIService")
    @patch("ai_lab.views.image.requests.get")
    def test_download_fails_with_bad_status_code(self, mock_requests_get, mock_openai_service):
        mock_service = MagicMock()
        mock_service.get_img_gen_response.return_value = "http://mocked.image.url/image.png"
        mock_openai_service.return_value = mock_service

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_requests_get.return_value = mock_response

        response = self.client.post(self.url, {"question": self.prompt}, content_type="application/json")

        self.assertEqual(response.status_code, 500)
        self.assertIn("Failed to download image", response.data["message"])

    @patch("ai_lab.views.image.OpenAIService")
    @patch("ai_lab.views.image.requests.get")
    def test_url_does_not_point_to_image(self, mock_requests_get, mock_openai_service):
        mock_service = MagicMock()
        mock_service.get_img_gen_response.return_value = "http://mocked.image.url/image.png"
        mock_openai_service.return_value = mock_service

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "text/html"}
        mock_requests_get.return_value = mock_response

        response = self.client.post(self.url, {"question": self.prompt}, content_type="application/json")

        self.assertEqual(response.status_code, 500)
        self.assertIn("URL does not point to an image", response.data["message"])


@override_settings(MEDIA_ROOT=os.path.join(tempfile.gettempdir(), "media"))
class AiLabImageDownloadViewTest(TestCase):

    def setUp(self):
        self.url = reverse("ai_lab:ai-lab-download-image")
        self.test_filename = "test-image.png"

        self.generated_images_dir = os.path.join(settings.MEDIA_ROOT, "generated_images")
        os.makedirs(self.generated_images_dir, exist_ok=True)

        self.test_file_path = os.path.join(self.generated_images_dir, self.test_filename)
        with open(self.test_file_path, "wb") as f:
            f.write(b"test image content")

    def tearDown(self):
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)

        if os.path.exists(self.generated_images_dir) and not os.listdir(self.generated_images_dir):
            os.rmdir(self.generated_images_dir)

        if os.path.exists(settings.MEDIA_ROOT) and not os.listdir(settings.MEDIA_ROOT):
            os.rmdir(settings.MEDIA_ROOT)

    def test_successful_file_download(self):
        response = self.client.post(self.url, {"filename": self.test_filename}, content_type="application/json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Disposition"], f'attachment; filename="{self.test_filename}"')
        self.assertEqual(response.getvalue(), b"test image content")

    def test_missing_filename_returns_400(self):
        response = self.client.post(self.url, {}, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "Filename is required.")

    def test_file_not_found_returns_404(self):
        response = self.client.post(self.url, {"filename": "nonexistent.png"}, content_type="application/json")
        self.assertEqual(response.status_code, 404)


@override_settings(MEDIA_ROOT=os.path.join(tempfile.gettempdir(), "media"))
class AiLabVoiceGeneratorViewTest(TestCase):

    def setUp(self):
        self.url = reverse("ai_lab:ai_lab_voice_generator")
        self.prompt = "Say something inspiring"

    @patch("ai_lab.views.voice.OpenAIService")
    @patch("ai_lab.views.voice.generate_file_name_with_extension", return_value="inspiring.mp3")
    def test_voice_generated_and_saved_successfully(self, mock_filename, mock_openai_service):
        mock_service = MagicMock()
        mock_message = MagicMock()
        mock_message.audio.data = b64encode(b"fake-audio-data").decode()
        mock_service.get_voice_gen_response.return_value = mock_message
        mock_openai_service.return_value = mock_service

        response = self.client.post(self.url, {"question": self.prompt}, content_type="application/json")

        self.assertEqual(response.status_code, 200)
        self.assertIn("generated_voices/inspiring.mp3", response.data["message"])

        full_path = os.path.join(settings.MEDIA_ROOT, "generated_voices", "inspiring.mp3")
        self.assertTrue(os.path.exists(full_path))

        os.remove(full_path)

    def test_missing_prompt_returns_400(self):
        response = self.client.post(self.url, {}, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "Prompt is required.")

    @patch("ai_lab.views.voice.OpenAIService")
    def test_service_failure_returns_500(self, mock_openai_service):
        mock_service = MagicMock()
        mock_service.get_voice_gen_response.side_effect = Exception("Something went wrong")
        mock_openai_service.return_value = mock_service

        response = self.client.post(self.url, {"question": self.prompt}, content_type="application/json")
        self.assertEqual(response.status_code, 500)
        self.assertIn("Something went wrong", response.data["message"])


@override_settings(MEDIA_ROOT=os.path.join(tempfile.gettempdir(), "media"))
class AiLabVisionImagesUploadViewTest(TestCase):

    def setUp(self):
        self.url = reverse("ai_lab:upload-vision-images")
        self.image = create_test_image("test-image.png")
        self.second_image = create_test_image("test-image.png")  # same name to test uniqueness
        self.vision_images_dir = os.path.join(settings.MEDIA_ROOT, "vision_images")

    def tearDown(self):
        if os.path.exists(self.vision_images_dir):
            for f in os.listdir(self.vision_images_dir):
                os.remove(os.path.join(self.vision_images_dir, f))
            os.rmdir(self.vision_images_dir)

    def test_upload_images_successfully(self):
        response = self.client.post(self.url, {"images[]": [self.image, self.second_image]}, format="multipart")

        self.assertEqual(response.status_code, 200)
        self.assertIn("uploaded_images", response.data)
        self.assertEqual(len(response.data["uploaded_images"]), 2)
        for url in response.data["uploaded_images"]:
            self.assertIn("vision_images/test-image", url)

        # Check files exist
        self.assertEqual(len(os.listdir(self.vision_images_dir)), 2)

    def test_upload_no_images_returns_400(self):
        response = self.client.post(self.url, {}, format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "No images provided.")
