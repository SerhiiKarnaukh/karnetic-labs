import json

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_lab.services import OpenAIService
from ai_lab.tools import TOOLS
from ai_lab.utils import StockAPI


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
