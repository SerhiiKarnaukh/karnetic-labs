from django.test import TestCase
from unittest.mock import patch, MagicMock
from ai_lab.services import OpenAIService


class OpenAIServiceConstructorTest(TestCase):
    @patch("ai_lab.services.openai.settings.OPENAI_API_KEY", "fake-key")
    @patch("openai.OpenAI")
    def test_constructor_calls_openai_with_correct_key(self, mock_openai):
        OpenAIService()
        mock_openai.assert_called_once_with(api_key="fake-key")


class OpenAIServiceTest(TestCase):

    @patch("ai_lab.services.openai.OpenAIService.__init__", return_value=None)
    def test_get_ai_response_success(self, mock_init):
        service = OpenAIService()
        service.client = MagicMock()

        mock_response = MagicMock()
        mock_response.output = [MagicMock(type="text", content=[MagicMock(text="Mocked response")])]
        service.client.responses.create.return_value = mock_response

        result = service.get_ai_response([{"role": "user", "content": "hi"}], tools=[])
        self.assertEqual(result.content[0].text, "Mocked response")

    @patch("ai_lab.services.openai.OpenAIService.__init__", return_value=None)
    def test_get_ai_response_exception(self, mock_init):
        service = OpenAIService()
        service.client = MagicMock()
        service.client.responses.create.side_effect = Exception("API failure")

        with self.assertRaises(Exception) as ctx:
            service.get_ai_response([], tools=[])

        self.assertIn("Error: API failure", str(ctx.exception))

    @patch("ai_lab.services.openai.OpenAIService.__init__", return_value=None)
    def test_get_img_gen_response_success(self, mock_init):
        service = OpenAIService()
        service.client = MagicMock()

        mock_response = MagicMock()
        mock_response.data = [MagicMock(url="http://example.com/image.png")]
        service.client.images.generate.return_value = mock_response

        result = service.get_img_gen_response("a cat with a hat")
        self.assertEqual(result, "http://example.com/image.png")

    @patch("ai_lab.services.openai.OpenAIService.__init__", return_value=None)
    def test_get_voice_gen_response_success(self, mock_init):
        service = OpenAIService()
        service.client = MagicMock()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message="Audio response")]
        service.client.chat.completions.create.return_value = mock_response

        result = service.get_voice_gen_response("say hello")
        self.assertEqual(result, "Audio response")

    @patch("ai_lab.services.openai.OpenAIService.__init__", return_value=None)
    def test_get_voice_gen_response_exception(self, mock_init):
        service = OpenAIService()
        service.client = MagicMock()
        service.client.chat.completions.create.side_effect = Exception("Audio error")

        with self.assertRaises(Exception) as ctx:
            service.get_voice_gen_response("boom")

        self.assertIn("Error: Audio error", str(ctx.exception))


class OpenAIServiceImgGenErrorTest(TestCase):

    @patch("ai_lab.services.openai.OpenAIService.__init__", return_value=None)
    def test_img_gen_raises_wrapped_exception(self, mock_init):
        service = OpenAIService()
        service.client = MagicMock()
        service.client.images.generate.side_effect = Exception("Something went wrong")

        with self.assertRaises(Exception) as ctx:
            service.get_img_gen_response("some prompt")

        self.assertIn("Error: Something went wrong", str(ctx.exception))
