"""API views for race control messages and flag status."""

from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from f1_pitwall.models import Session
from f1_pitwall.serializers.race_control import RaceControlMessageSerializer
from f1_pitwall.services.race_control_service import RaceControlService


class RaceControlListView(ListAPIView):
    """GET /race-control/<session>/ all race control messages."""

    serializer_class = RaceControlMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        session_key = self.kwargs['session_key']
        get_object_or_404(Session, session_key=session_key)
        return RaceControlService().get_messages(session_key)


class RaceControlFlagsView(APIView):
    """GET /race-control/<session>/flags/ latest flag state."""

    permission_classes = [IsAuthenticated]

    def get(self, request, session_key):
        get_object_or_404(Session, session_key=session_key)
        service = RaceControlService()
        latest_flag = service.get_latest_flag(session_key)
        return Response({
            'session_key': session_key,
            'latest_flag': latest_flag,
            'safety_car_active': service.is_safety_car_active(session_key),
        })
