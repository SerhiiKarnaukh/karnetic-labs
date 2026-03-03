"""Tests for F1 WebSocket routing and ASGI integration."""

from django.test import SimpleTestCase

from f1_pitwall.routing import websocket_urlpatterns
from portfolio import asgi


class F1WebSocketRoutingTest(SimpleTestCase):
    """Ensure F1 websocket routes are exposed."""

    def test_has_telemetry_route_pattern(self):
        patterns = [str(p.pattern) for p in websocket_urlpatterns]
        self.assertIn('^ws/f1/telemetry/(?P<session_key>\\d+)/$', patterns)

    def test_has_race_control_route_pattern(self):
        patterns = [str(p.pattern) for p in websocket_urlpatterns]
        self.assertIn('^ws/f1/race-control/$', patterns)


class AsgiWebSocketIntegrationTest(SimpleTestCase):
    """Ensure ASGI router includes F1 websocket routes."""

    def test_asgi_loads_f1_ws_patterns(self):
        patterns = [str(p.pattern) for p in asgi.ws_patterns]
        self.assertIn('^ws/f1/telemetry/(?P<session_key>\\d+)/$', patterns)
        self.assertIn('^ws/f1/race-control/$', patterns)

    def test_asgi_application_exposes_websocket_protocol(self):
        self.assertIn('websocket', asgi.application.application_mapping)
