"""API views for strategy calculation and stint data."""

from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from f1_pitwall.models import Session, Stint
from f1_pitwall.serializers.strategy import (
    StintSerializer,
    StrategyCalculateRequestSerializer,
    StrategyOptionSerializer,
)
from f1_pitwall.services.strategy_engine import StrategyEngine


class StrategyCalculateView(APIView):
    """POST /strategy/<session>/calculate/ strategy endpoint."""

    permission_classes = [IsAuthenticated]

    def post(self, request, session_key):
        session = get_object_or_404(Session, session_key=session_key)
        serializer = StrategyCalculateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        engine = StrategyEngine()
        strategies = engine.calculate_strategies(**serializer.validated_data)
        options = StrategyOptionSerializer(strategies, many=True)
        return Response({
            'session_key': session.session_key,
            'count': len(strategies),
            'strategies': options.data,
        })


class StrategyStintsView(ListAPIView):
    """GET /strategy/<session>/stints/ endpoint."""

    serializer_class = StintSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        session = get_object_or_404(
            Session, session_key=self.kwargs['session_key'],
        )
        return Stint.objects.filter(session=session).order_by(
            'driver__driver_number', 'stint_number',
        )
