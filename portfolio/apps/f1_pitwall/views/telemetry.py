"""API views for telemetry data retrieval."""

from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from f1_pitwall.models import Session, TelemetrySnapshot
from f1_pitwall.serializers.telemetry import TelemetrySnapshotSerializer
from f1_pitwall.services.session_data_hydrator import SessionDataHydrator


class TelemetryListView(ListAPIView):
    """GET /telemetry/<session>/ with driver and time filters."""

    serializer_class = TelemetrySnapshotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        session_key = self.kwargs['session_key']
        session = get_object_or_404(Session, session_key=session_key)
        driver = self.request.query_params.get('driver')
        SessionDataHydrator().ensure_latest_snapshots(session, driver)
        queryset = TelemetrySnapshot.objects.filter(session=session)

        if driver:
            queryset = queryset.filter(driver__driver_number=driver)

        date_from = parse_datetime(self.request.query_params.get('date_from', ''))
        if date_from:
            queryset = queryset.filter(timestamp__gte=date_from)

        date_to = parse_datetime(self.request.query_params.get('date_to', ''))
        if date_to:
            queryset = queryset.filter(timestamp__lte=date_to)

        return queryset.order_by('timestamp')


class TelemetryLatestView(ListAPIView):
    """GET /telemetry/<session>/latest/ returns latest row per driver."""

    serializer_class = TelemetrySnapshotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        session_key = self.kwargs['session_key']
        session = get_object_or_404(Session, session_key=session_key)
        SessionDataHydrator().ensure_latest_snapshots(session)
        base = TelemetrySnapshot.objects.filter(session=session)

        latest_by_driver = base.filter(
            driver=OuterRef('driver'),
        ).order_by('-timestamp').values('id')[:1]

        return base.filter(
            id__in=Subquery(latest_by_driver),
        ).order_by('driver__driver_number')
