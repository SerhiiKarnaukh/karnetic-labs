from django.urls import path

from ai_lab import views

app_name = 'ai_lab'

urlpatterns = [
    path('', views.AiLabChatView.as_view(), name='ai_lab_api'),
    path('image-generator/', views.AiLabImageGeneratorView.as_view(), name='ai_lab_image_generator'),
    path('voice-generator/', views.AiLabVoiceGeneratorView.as_view(), name='ai_lab_voice_generator'),
    path('download-image/', views.AiLabImageDownloadView.as_view(), name='ai-lab-download-image'),
    path('upload-vision-images/', views.AiLabVisionImagesUploadView.as_view(), name='upload-vision-images'),
    path('delete-vision-image/', views.AiLabVisionImageDeleteView.as_view(), name='delete-vision-image'),
    path('realtime-token/', views.AiLabRealtimeTokenView.as_view(), name='realtime-token'),
]
