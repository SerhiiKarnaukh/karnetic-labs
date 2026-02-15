"""API views for session list, detail, and live session detection."""

from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from f1_pitwall.models import Session
from f1_pitwall.serializers.session import (
    SessionDetailSerializer,
    SessionListSerializer,
)


class SessionListView(ListAPIView):
    """List sessions with optional filtering by year, type, and circuit."""

    serializer_class = SessionListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Session.objects.all()
        year = self.request.query_params.get('year')
        session_type = self.request.query_params.get('type')
        circuit = self.request.query_params.get('circuit')

        if year:
            queryset = queryset.filter(year=year)
        if session_type:
            queryset = queryset.filter(session_type=session_type)
        if circuit:
            queryset = queryset.filter(circuit_short_name__icontains=circuit)

        return queryset


class SessionDetailView(RetrieveAPIView):
    """Retrieve a single session by its OpenF1 session_key."""

    serializer_class = SessionDetailSerializer
    permission_classes = [IsAuthenticated]
    queryset = Session.objects.all()
    lookup_field = 'session_key'
    lookup_url_kwarg = 'session_key'


class SessionLiveView(APIView):
    """Return the currently live session, if any."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        session = Session.objects.filter(is_live=True).first()
        if session is None:
            return Response(
                {'detail': 'No live session at this time.'},
                status=200,
            )
        serializer = SessionDetailSerializer(session)
        return Response(serializer.data)
