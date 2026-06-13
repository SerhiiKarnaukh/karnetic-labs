import requests
from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_lab.utils.errors import build_ai_lab_error_from_http_body, build_ai_lab_error_response
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
                data, status = build_ai_lab_error_from_http_body(
                    response.text,
                    default_message="Failed to get realtime token.",
                )
                return Response(data, status=status)

            return Response(_normalize_client_secret_response(response.json()))

        except Exception as e:
            data, status = build_ai_lab_error_response(e)
            return Response(data, status=status)
