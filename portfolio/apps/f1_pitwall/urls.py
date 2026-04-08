"""URL configuration for the F1 Pit Wall API endpoints."""

from django.urls import path

from f1_pitwall.views.auth import F1MeView, F1RegisterView
from f1_pitwall.views.drivers import DriverDetailView, DriverListView
from f1_pitwall.views.laps import FastestLapsView, LapDataListView
from f1_pitwall.views.race_control import RaceControlFlagsView, RaceControlListView
from f1_pitwall.views.session import (
    SessionDetailView,
    SessionListView,
    SessionLiveView,
)
from f1_pitwall.views.strategy import StrategyCalculateView, StrategyStintsView
from f1_pitwall.views.telemetry import TelemetryLatestView, TelemetryListView
from f1_pitwall.views.weather import (
    WeatherCurrentView,
    WeatherForecastView,
    WeatherTimelineView,
)

app_name = 'f1_pitwall'

urlpatterns = [
    # Auth
    path(
        'api/register/',
        F1RegisterView.as_view(),
        name='register',
    ),
    path(
        'api/me/',
        F1MeView.as_view(),
        name='me',
    ),

    # Sessions
    path(
        'api/sessions/',
        SessionListView.as_view(),
        name='session-list',
    ),
    path(
        'api/sessions/live/',
        SessionLiveView.as_view(),
        name='session-live',
    ),
    path(
        'api/sessions/<int:session_key>/',
        SessionDetailView.as_view(),
        name='session-detail',
    ),

    # Drivers
    path(
        'api/drivers/',
        DriverListView.as_view(),
        name='driver-list',
    ),
    path(
        'api/drivers/<int:driver_number>/',
        DriverDetailView.as_view(),
        name='driver-detail',
    ),

    # Telemetry
    path(
        'api/telemetry/<int:session_key>/',
        TelemetryListView.as_view(),
        name='telemetry-list',
    ),
    path(
        'api/telemetry/<int:session_key>/latest/',
        TelemetryLatestView.as_view(),
        name='telemetry-latest',
    ),

    # Laps
    path(
        'api/laps/<int:session_key>/',
        LapDataListView.as_view(),
        name='lap-list',
    ),
    path(
        'api/laps/<int:session_key>/fastest/',
        FastestLapsView.as_view(),
        name='lap-fastest',
    ),

    # Strategy
    path(
        'api/strategy/<int:session_key>/calculate/',
        StrategyCalculateView.as_view(),
        name='strategy-calculate',
    ),
    path(
        'api/strategy/<int:session_key>/stints/',
        StrategyStintsView.as_view(),
        name='strategy-stints',
    ),

    # Weather
    path(
        'api/weather/<int:session_key>/',
        WeatherTimelineView.as_view(),
        name='weather-timeline',
    ),
    path(
        'api/weather/<int:session_key>/current/',
        WeatherCurrentView.as_view(),
        name='weather-current',
    ),
    path(
        'api/weather/<int:session_key>/forecast/',
        WeatherForecastView.as_view(),
        name='weather-forecast',
    ),

    # Race control
    path(
        'api/race-control/<int:session_key>/',
        RaceControlListView.as_view(),
        name='race-control-list',
    ),
    path(
        'api/race-control/<int:session_key>/flags/',
        RaceControlFlagsView.as_view(),
        name='race-control-flags',
    ),
]
