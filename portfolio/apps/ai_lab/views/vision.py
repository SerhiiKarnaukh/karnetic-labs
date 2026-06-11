import os
import uuid

from django.conf import settings
from django.core.files.storage import default_storage
from django.utils.text import slugify
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


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

            if default_storage.exists(os.path.join('vision_images', full_filename)):
                short_hash = uuid.uuid4().hex[:8]
                full_filename = f"{filename}-{short_hash}{extension}"

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


class AiLabVisionImageDeleteView(APIView):
    permission_classes = [AllowAny]

    def delete(self, request):
        filename = request.data.get("filename")
        if not filename:
            return Response({"error": "Filename is required."}, status=400)

        safe_filename = os.path.basename(filename)
        if safe_filename != filename:
            return Response({"error": "Invalid filename."}, status=400)

        file_path = os.path.join(settings.MEDIA_ROOT, 'vision_images', safe_filename)

        if not os.path.exists(file_path):
            return Response({"error": "File not found."}, status=404)

        os.remove(file_path)
        return Response({"message": f"File '{safe_filename}' deleted successfully."})
