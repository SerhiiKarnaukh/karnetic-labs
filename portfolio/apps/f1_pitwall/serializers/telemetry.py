"""Serializers for the TelemetrySnapshot model."""

from rest_framework import serializers

from f1_pitwall.models import TelemetrySnapshot


class TelemetrySnapshotSerializer(serializers.ModelSerializer):
    """Serializer for telemetry snapshot payloads."""

    driver_number = serializers.IntegerField(source='driver.driver_number')
    session_key = serializers.IntegerField(source='session.session_key')

    class Meta:
        model = TelemetrySnapshot
        fields = (
            'id',
            'session_key',
            'driver_number',
            'timestamp',
            'speed',
            'rpm',
            'throttle',
            'brake',
            'gear',
            'drs',
            'data_source',
            'is_fallback',
        )
