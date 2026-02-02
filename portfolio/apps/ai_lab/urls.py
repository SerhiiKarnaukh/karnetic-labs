from django.urls import path

from . import api

app_name = 'ai_lab'

urlpatterns = [
    path('', api.AiLabChatView.as_view(), name='ai_lab_api'),
    path('image-generator/', api.AiLabImageGeneratorView.as_view(), name='ai_lab_image_generator'),
    path('voice-generator/', api.AiLabVoiceGeneratorView.as_view(), name='ai_lab_voice_generator'),
    path('download-image/', api.AiLabImageDownloadView.as_view(), name='ai-lab-download-image'),
    path('upload-vision-images/', api.AiLabVisionImagesUploadView.as_view(), name='upload-vision-images'),
    path('realtime-token/', api.AiLabRealtimeTokenView.as_view(), name='realtime-token'),
]
