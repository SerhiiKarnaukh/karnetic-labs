"""API views for lap data and fastest laps."""

from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from f1_pitwall.models import LapData, Session
from f1_pitwall.serializers.laps import LapDataSerializer
from f1_pitwall.services.session_data_hydrator import SessionDataHydrator


class LapDataListView(ListAPIView):
    """Return lap records for a session."""

    serializer_class = LapDataSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        session = self._get_session()
        driver_number = self.request.query_params.get('driver')
        SessionDataHydrator().ensure_laps(session, driver_number)
        queryset = LapData.objects.filter(session=session)

        if driver_number:
            queryset = queryset.filter(driver__driver_number=driver_number)

        return queryset.order_by('driver__driver_number', 'lap_number')

    def _get_session(self):
        return get_object_or_404(Session, session_key=self.kwargs['session_key'])


class FastestLapsView(ListAPIView):
    """Return fastest valid lap per driver for a session."""

    serializer_class = LapDataSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        session = self._get_session()
        SessionDataHydrator().ensure_laps(session)
        base = LapData.objects.filter(
            session=session,
            lap_duration__isnull=False,
        )
        fastest_per_driver = base.filter(
            driver=OuterRef('driver'),
        ).order_by('lap_duration', 'lap_number').values('id')[:1]
        return base.filter(id__in=Subquery(fastest_per_driver)).order_by(
            'driver__driver_number',
        )

    def _get_session(self):
        return get_object_or_404(Session, session_key=self.kwargs['session_key'])
