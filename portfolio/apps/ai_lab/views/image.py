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
            image_url = self.generate_image(prompt)
            full_url = self.download_and_save_image(image_url, prompt, request)

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
