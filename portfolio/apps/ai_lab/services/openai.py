from django.conf import settings


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
                model="dall-e-3", prompt=prompt,
            )
            return response.data[0].url
        except Exception as e:
            raise Exception(f"Error: {str(e)}")

    def get_voice_gen_response(self, prompt):
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-audio-preview",
                modalities=["text", "audio"],
                audio={"voice": "verse", "format": "mp3"},
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message
        except Exception as e:
            raise Exception(f"Error: {str(e)}")
