import os
import requests
import json
from base64 import b64decode

from django.conf import settings
from django.http import FileResponse, Http404
from django.core.files.storage import default_storage
from django.utils.text import slugify

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .tools import TOOLS
from .utils import StockAPI, generate_file_name_with_extension
from .services import OpenAIService


class AiLabChatView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        question = request.data.get("question")
        prompt_images = request.data.get("prompt_images", [])

        openai_service = OpenAIService()
        available_functions = {"get_stock_price": StockAPI.get_stock_price}

        user_content = [
            {"type": "input_text", "text": question},
        ]

        if prompt_images:
            for url in prompt_images:
                user_content.append({
                    "type": "input_image",
                    "image_url": url,
                    "detail": "low",
                })

        messages = [
            {"role": "system", "content": "Answer briefly - no more than five sentences and in the form of a joke."},
            {"role": "user", "content": user_content},
        ]

        try:

            response_output = openai_service.get_ai_response(messages, TOOLS)

            if response_output.type == "function_call":
                function_name = response_output.name
                function_args = json.loads(response_output.arguments)
                function_response = available_functions[function_name](**function_args)
                messages.append(response_output)
                tool_response_message = {
                    "type": "function_call_output",
                    "call_id": response_output.call_id,
                    "output": json.dumps(function_response),
                }
                messages.append(tool_response_message)

                second_response = openai_service.get_ai_response(messages, TOOLS)

                return Response({"message": second_response.content[0].text})

            return Response({"message": response_output.content[0].text})

        except Exception as e:
            return Response({"message": str(e)}, status=500)


class AiLabImageGeneratorView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        prompt = request.data.get("question")
        if not prompt:
            return Response({"error": "Prompt is required."}, status=400)

        try:
            image_url = self.generate_image(prompt)
            full_url = self.download_and_save_image(image_url, prompt,  request)

            return Response({"message": full_url})
        except Exception as e:
            return Response({"message": str(e)}, status=500)

    def generate_image(self, prompt):
        openai_service = OpenAIService()
        return openai_service.get_img_gen_response(prompt)

    def download_and_save_image(self, image_url, prompt, request):
        img_response = requests.get(image_url, stream=True)
        if img_response.status_code != 200:
            raise Exception("Failed to download image.")

        content_type = img_response.headers.get("Content-Type")
        if not content_type or not content_type.startswith("image/"):
            raise Exception("URL does not point to an image.")

        generated_images_dir = os.path.join(settings.MEDIA_ROOT, "generated_images")
        os.makedirs(generated_images_dir, exist_ok=True)
        filename = generate_file_name_with_extension(prompt, generated_images_dir, "png")

        filepath = os.path.join(generated_images_dir, filename)
        with open(filepath, "wb") as f:
            for chunk in img_response.iter_content(1024):
                f.write(chunk)

        media_url = os.path.join(settings.MEDIA_URL, "generated_images", filename)
        full_url = request.build_absolute_uri(media_url)
        return full_url


class AiLabImageDownloadView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        image_name = request.data.get("filename")
        if not image_name:
            return Response({"error": "Filename is required."}, status=400)

        file_path = os.path.join(settings.MEDIA_ROOT, "generated_images", image_name)
        if not os.path.exists(file_path):
            raise Http404("File not found.")

        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=image_name)


class AiLabVoiceGeneratorView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        prompt = request.data.get("question")
        if not prompt:
            return Response({"error": "Prompt is required."}, status=400)

        try:
            message = self.generate_voice(prompt)
            full_url = self.save_voice(message, prompt,  request)

            return Response({"message": full_url})
        except Exception as e:
            return Response({"message": str(e)}, status=500)

    def generate_voice(self, prompt):
        openai_service = OpenAIService()
        return openai_service.get_voice_gen_response(prompt)

    def save_voice(self, message, prompt, request):

        generated_voices_dir = os.path.join(settings.MEDIA_ROOT, "generated_voices")
        os.makedirs(generated_voices_dir, exist_ok=True)

        filename = generate_file_name_with_extension(prompt, generated_voices_dir, "mp3")

        filepath = os.path.join(generated_voices_dir, filename)
        with open(filepath, "wb") as f:
            f.write(b64decode(message.audio.data))

        media_path = os.path.join(settings.MEDIA_URL, "generated_voices", filename)

        scheme = "https" if not settings.DEBUG else request.scheme
        host = request.get_host()

        full_url = f"{scheme}://{host}{media_path}"
        return full_url


class AiLabVisionImagesUploadView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        images = request.FILES.getlist('images[]')
        if not images:
            return Response({"error": "No images provided."}, status=400)

        saved_image_urls = []

        vision_images_dir = os.path.join(settings.MEDIA_ROOT, 'vision_images')
        os.makedirs(vision_images_dir, exist_ok=True)

        for image in images:
            filename = slugify(os.path.splitext(image.name)[0])
            extension = os.path.splitext(image.name)[1]
            full_filename = f"{filename}{extension}"

            counter = 1
            while default_storage.exists(os.path.join('vision_images', full_filename)):
                full_filename = f"{filename}-{counter}{extension}"
                counter += 1

            filepath = os.path.join('vision_images', full_filename)
            full_file_path = os.path.join(settings.MEDIA_ROOT, filepath)

            with open(full_file_path, 'wb+') as f:
                for chunk in image.chunks():
                    f.write(chunk)

            scheme = "https" if not settings.DEBUG else request.scheme
            host = request.get_host()
            file_url = f"{scheme}://{host}{settings.MEDIA_URL}vision_images/{full_filename}"
            saved_image_urls.append(file_url)

        return Response({"uploaded_images": saved_image_urls})


class AiLabRealtimeTokenView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        try:
            response = requests.post(
                'https://api.openai.com/v1/realtime/sessions',
                headers={
                    'Authorization': f'Bearer {settings.OPENAI_API_KEY}',
                    'Content-Type': 'application/json',
                    'OpenAI-Beta': 'realtime=v1'
                },
                json={
                    'model': 'gpt-4o-realtime-preview-2024-12-17',
                    'voice': 'alloy'
                }
            )

            if response.status_code == 200:
                return Response(response.json())
            else:
                return Response(
                    {"error": "Failed to get token", "details": response.text},
                    status=500
                )

        except Exception as e:
            return Response({"error": str(e)}, status=500)
