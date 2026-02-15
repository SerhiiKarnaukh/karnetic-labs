"""URL configuration for the F1 Pit Wall API endpoints."""

from django.urls import path

from f1_pitwall.views.drivers import DriverDetailView, DriverListView
from f1_pitwall.views.session import (
    SessionDetailView,
    SessionListView,
    SessionLiveView,
)

app_name = 'f1_pitwall'

urlpatterns = [
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
]
