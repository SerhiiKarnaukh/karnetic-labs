"""API views for weather data and rain forecast."""

from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from f1_pitwall.models import Session
from f1_pitwall.serializers.weather import (
    WeatherDataSerializer,
    WeatherForecastSerializer,
)
from f1_pitwall.services.weather_service import WeatherService


class WeatherTimelineView(ListAPIView):
    """GET /weather/<session>/ timeline endpoint."""

    serializer_class = WeatherDataSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        session_key = self.kwargs['session_key']
        get_object_or_404(Session, session_key=session_key)
        return WeatherService().get_weather_history(session_key)


class WeatherCurrentView(APIView):
    """GET /weather/<session>/current/ endpoint."""

    permission_classes = [IsAuthenticated]

    def get(self, request, session_key):
        get_object_or_404(Session, session_key=session_key)
        weather = WeatherService().get_current_weather(session_key)
        if weather is None:
            return Response(
                {'detail': 'No weather data available for this session.'},
                status=200,
            )
        serializer = WeatherDataSerializer(weather)
        return Response(serializer.data)


class WeatherForecastView(APIView):
    """GET /weather/<session>/forecast/ endpoint."""

    permission_classes = [IsAuthenticated]

    def get(self, request, session_key):
        get_object_or_404(Session, session_key=session_key)
        forecast = WeatherService().calculate_rain_forecast(session_key)
        serializer = WeatherForecastSerializer(forecast)
        return Response(serializer.data)
