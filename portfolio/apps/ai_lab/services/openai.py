from django.conf import settings

IMAGE_GEN_MODEL = "gpt-image-1"
VOICE_GEN_MODEL = "gpt-audio-1.5"


class OpenAIService:
    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def get_ai_response(self, messages, tools):
        try:
            response = self.client.responses.create(
                model="gpt-4o", input=messages, tools=tools
            )
            return response.output[0]
        except Exception as e:
            raise Exception(f"Error: {str(e)}")

    def get_img_gen_response(self, prompt):
        try:
            response = self.client.images.generate(
                model=IMAGE_GEN_MODEL,
                prompt=prompt,
                size="1024x1024",
            )
            image = response.data[0]
            if image.url:
                return image.url
            if image.b64_json:
                return image.b64_json
            raise Exception("No image data in response")
        except Exception as e:
            raise Exception(f"Error: {str(e)}")

    def get_voice_gen_response(self, prompt):
        try:
            response = self.client.chat.completions.create(
                model=VOICE_GEN_MODEL,
                modalities=["text", "audio"],
                audio={"voice": "verse", "format": "mp3"},
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message
        except Exception as e:
            raise Exception(f"Error: {str(e)}")
