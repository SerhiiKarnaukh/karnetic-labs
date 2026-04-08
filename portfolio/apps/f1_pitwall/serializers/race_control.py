"""Serializers for race control API endpoints."""

from rest_framework import serializers

from f1_pitwall.models import RaceControlMessage


class RaceControlMessageSerializer(serializers.ModelSerializer):
    """Serialize race control message rows."""

    session_key = serializers.IntegerField(source='session.session_key')

    class Meta:
        model = RaceControlMessage
        fields = (
            'id',
            'session_key',
            'timestamp',
            'category',
            'message',
            'flag',
            'driver_number',
            'lap_number',
            'sector',
        )
