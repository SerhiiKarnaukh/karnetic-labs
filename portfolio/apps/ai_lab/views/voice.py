import os
from base64 import b64decode

from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_lab.services import OpenAIService
from ai_lab.utils import generate_file_name_with_extension


class AiLabVoiceGeneratorView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        prompt = request.data.get("question")
        if not prompt:
            return Response({"error": "Prompt is required."}, status=400)

        try:
            message = self.generate_voice(prompt)
            full_url = self.save_voice(message, prompt, request)

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
