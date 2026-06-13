import json

OPENAI_QUOTA_EXCEEDED_CODE = "openai_quota_exceeded"
OPENAI_QUOTA_EXCEEDED_MESSAGE = (
    "OpenAI API credits have been exhausted. "
    "AI Lab features are temporarily unavailable. "
    "Please contact the site administrator."
)

_QUOTA_MARKERS = (
    "insufficient_quota",
    "exceeded your current quota",
    "billing",
    "credit balance",
    "payment required",
)


def is_openai_quota_error(error):
    return _contains_quota_marker(_extract_error_text(error))


def build_ai_lab_error_response(error):
    if is_openai_quota_error(error):
        return _quota_exceeded_response()
    return {"message": str(error)}, 500


def build_ai_lab_error_from_http_body(body, default_message):
    if is_openai_quota_error(body):
        return _quota_exceeded_response()
    return {"message": default_message, "details": body}, 500


def _quota_exceeded_response():
    return {
        "message": OPENAI_QUOTA_EXCEEDED_MESSAGE,
        "error_code": OPENAI_QUOTA_EXCEEDED_CODE,
    }, 402


def _extract_error_text(error):
    parts = [str(error)]

    body = getattr(error, "body", None)
    if body is not None:
        parts.append(json.dumps(body) if isinstance(body, dict) else str(body))

    for attr in ("message", "code"):
        value = getattr(error, attr, None)
        if value:
            parts.append(str(value))

    return " ".join(parts)


def _contains_quota_marker(text):
    lowered = text.lower()
    return any(marker in lowered for marker in _QUOTA_MARKERS)
