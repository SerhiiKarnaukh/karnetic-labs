"""WebSocket URL routing for telemetry and race control consumers."""

from django.urls import re_path

from .consumers.race_control import RaceControlConsumer
from .consumers.telemetry import TelemetryConsumer

websocket_urlpatterns = [
    re_path(
        r'^ws/f1/telemetry/(?P<session_key>\d+)/$',
        TelemetryConsumer.as_asgi(),
    ),
    re_path(
        r'^ws/f1/race-control/$',
        RaceControlConsumer.as_asgi(),
    ),
]
