from django.urls import re_path

from .websocket import consumers

websocket_urlpatterns = [
    re_path(
        r'ws/social-chat/(?P<conversation_id>[0-9a-f-]+)/(?P<user_id>\d+)/$',
        consumers.SocialChatConsumer.as_asgi(),
    ),
    re_path(
        r'wss/social-chat/(?P<conversation_id>[0-9a-f-]+)/(?P<user_id>\d+)/$',
        consumers.SocialChatConsumer.as_asgi(),
    ),
]
