"""API views for driver list and detail."""

from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from f1_pitwall.models import Driver
from f1_pitwall.serializers.driver import (
    DriverDetailSerializer,
    DriverListSerializer,
)


class DriverListView(ListAPIView):
    """List all active drivers with team info."""

    serializer_class = DriverListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Driver.objects.all()
        active_only = self.request.query_params.get('active')

        if active_only is not None and active_only.lower() in ('true', '1'):
            queryset = queryset.filter(is_active=True)

        return queryset


class DriverDetailView(RetrieveAPIView):
    """Retrieve a single driver by car number."""

    serializer_class = DriverDetailSerializer
    permission_classes = [IsAuthenticated]
    queryset = Driver.objects.all()
    lookup_field = 'driver_number'
    lookup_url_kwarg = 'driver_number'
