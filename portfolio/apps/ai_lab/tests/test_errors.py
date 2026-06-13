from django.test import TestCase

from ai_lab.utils.errors import (
    OPENAI_QUOTA_EXCEEDED_CODE,
    OPENAI_QUOTA_EXCEEDED_MESSAGE,
    build_ai_lab_error_from_http_body,
    build_ai_lab_error_response,
    is_openai_quota_error,
)


class OpenAIQuotaErrorTest(TestCase):
    def test_detects_insufficient_quota_in_exception_text(self):
        error = Exception(
            "Error: Error code: 429 - {'error': {'code': 'insufficient_quota'}}"
        )
        self.assertTrue(is_openai_quota_error(error))

    def test_build_ai_lab_error_response_returns_quota_payload(self):
        error = Exception("insufficient_quota")
        data, status = build_ai_lab_error_response(error)

        self.assertEqual(status, 402)
        self.assertEqual(data["message"], OPENAI_QUOTA_EXCEEDED_MESSAGE)
        self.assertEqual(data["error_code"], OPENAI_QUOTA_EXCEEDED_CODE)

    def test_build_ai_lab_error_response_returns_generic_error(self):
        error = Exception("Something went wrong")
        data, status = build_ai_lab_error_response(error)

        self.assertEqual(status, 500)
        self.assertEqual(data["message"], "Something went wrong")
        self.assertNotIn("error_code", data)

    def test_build_ai_lab_error_from_http_body_returns_quota_payload(self):
        body = '{"error":{"code":"insufficient_quota","message":"You exceeded your current quota"}}'
        data, status = build_ai_lab_error_from_http_body(body, "Failed to get realtime token.")

        self.assertEqual(status, 402)
        self.assertEqual(data["error_code"], OPENAI_QUOTA_EXCEEDED_CODE)

    def test_build_ai_lab_error_from_http_body_returns_generic_error(self):
        body = '{"error":{"message":"Invalid URL"}}'
        data, status = build_ai_lab_error_from_http_body(body, "Failed to get realtime token.")

        self.assertEqual(status, 500)
        self.assertEqual(data["message"], "Failed to get realtime token.")
        self.assertEqual(data["details"], body)
