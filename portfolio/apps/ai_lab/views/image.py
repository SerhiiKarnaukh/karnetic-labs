import base64
import os

import requests
from django.conf import settings
from django.http import FileResponse, Http404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_lab.services import OpenAIService
from ai_lab.utils import generate_file_name_with_extension


class AiLabImageGeneratorView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        prompt = request.data.get("question")
        if not prompt:
            return Response({"error": "Prompt is required."}, status=400)

        try:
            image_result = self.generate_image(prompt)
            full_url = self.save_generated_image(image_result, prompt, request)

            return Response({"message": full_url})
        except Exception as e:
            return Response({"message": str(e)}, status=500)

    def generate_image(self, prompt):
        openai_service = OpenAIService()
        return openai_service.get_img_gen_response(prompt)

    def save_generated_image(self, image_result, prompt, request):
        filepath, filename = self._prepare_generated_filepath(prompt)

        if image_result.startswith("http"):
            self._write_image_from_url(image_result, filepath)
        else:
            self._write_image_from_base64(image_result, filepath)

        return self._build_generated_image_url(filename, request)

    def _prepare_generated_filepath(self, prompt):
        generated_images_dir = os.path.join(settings.MEDIA_ROOT, "generated_images")
        os.makedirs(generated_images_dir, exist_ok=True)
        filename = generate_file_name_with_extension(prompt, generated_images_dir, "png")
        filepath = os.path.join(generated_images_dir, filename)
        return filepath, filename

    def _write_image_from_url(self, image_url, filepath):
        img_response = requests.get(image_url, stream=True)
        if img_response.status_code != 200:
            raise Exception("Failed to download image.")

        content_type = img_response.headers.get("Content-Type")
        if not content_type or not content_type.startswith("image/"):
            raise Exception("URL does not point to an image.")

        with open(filepath, "wb") as f:
            for chunk in img_response.iter_content(1024):
                f.write(chunk)

    def _write_image_from_base64(self, image_b64, filepath):
        with open(filepath, "wb") as f:
            f.write(base64.b64decode(image_b64))

    def _build_generated_image_url(self, filename, request):
        media_url = os.path.join(settings.MEDIA_URL, "generated_images", filename)
        return request.build_absolute_uri(media_url)


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
