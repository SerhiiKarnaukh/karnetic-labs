from django.urls import re_path

from .websocket import consumers

websocket_urlpatterns = [
    re_path(
        r'ws/notification/(?P<user_id>\d+)/$',
        consumers.NotificationConsumer.as_asgi(),
    ),
    re_path(
        r'wss/notification/(?P<user_id>\d+)/$',
        consumers.NotificationConsumer.as_asgi(),
    ),
]
