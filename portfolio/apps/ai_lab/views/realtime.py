import requests
from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

REALTIME_MODEL = "gpt-realtime"
REALTIME_CLIENT_SECRETS_URL = "https://api.openai.com/v1/realtime/client_secrets"


def _build_session_payload():
    return {
        "session": {
            "type": "realtime",
            "model": REALTIME_MODEL,
            "output_modalities": ["text"],
        }
    }


def _normalize_client_secret_response(data):
    if "client_secret" in data:
        return data

    session = data.get("session", {})
    return {
        **session,
        "client_secret": {
            "value": data["value"],
            "expires_at": data.get("expires_at"),
        },
    }


class AiLabRealtimeTokenView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        try:
            response = requests.post(
                REALTIME_CLIENT_SECRETS_URL,
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=_build_session_payload(),
                timeout=15,
            )

            if response.status_code != 200:
                return Response(
                    {"error": "Failed to get token", "details": response.text},
                    status=500,
                )

            return Response(_normalize_client_secret_response(response.json()))

        except Exception as e:
            return Response({"error": str(e)}, status=500)
