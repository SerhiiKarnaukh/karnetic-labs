import requests
from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


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
