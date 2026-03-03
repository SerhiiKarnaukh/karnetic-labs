"""
ASGI config for portfolio project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio.settings')
django_asgi_app = get_asgi_application()
ws_patterns = []


def _load_websocket_patterns():
    from .apps.f1_pitwall import routing as f1_pitwall_routing
    from .apps.social_chat import routing as social_chat_routing
    from .apps.social_notification import routing as social_notification_routing

    return (
        social_chat_routing.websocket_urlpatterns
        + social_notification_routing.websocket_urlpatterns
        + f1_pitwall_routing.websocket_urlpatterns
    )


ws_patterns = _load_websocket_patterns()


if os.environ.get('DEBUG') == 'True':
    application = ProtocolTypeRouter({
        'http':
        ASGIStaticFilesHandler(django_asgi_app),
        'websocket':
        AuthMiddlewareStack(
            URLRouter(ws_patterns))

    })
else:
    application = ProtocolTypeRouter({
        'http':
        django_asgi_app,
        'websocket':
        AuthMiddlewareStack(
            URLRouter(ws_patterns))
    })
