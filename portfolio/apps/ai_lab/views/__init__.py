from ai_lab.views.chat import AiLabChatView
from ai_lab.views.image import AiLabImageDownloadView, AiLabImageGeneratorView
from ai_lab.views.realtime import AiLabRealtimeTokenView
from ai_lab.views.vision import AiLabVisionImageDeleteView, AiLabVisionImagesUploadView
from ai_lab.views.voice import AiLabVoiceGeneratorView

__all__ = [
    'AiLabChatView',
    'AiLabImageDownloadView',
    'AiLabImageGeneratorView',
    'AiLabRealtimeTokenView',
    'AiLabVisionImageDeleteView',
    'AiLabVisionImagesUploadView',
    'AiLabVoiceGeneratorView',
]
