"""Serializers for lap timing API endpoints."""

from rest_framework import serializers

from f1_pitwall.models import LapData


class LapDataSerializer(serializers.ModelSerializer):
    """Serialize lap timing records for API responses."""

    session_key = serializers.IntegerField(source='session.session_key')
    driver_number = serializers.IntegerField(source='driver.driver_number')

    class Meta:
        model = LapData
        fields = (
            'id',
            'session_key',
            'driver_number',
            'lap_number',
            'lap_duration',
            'sector_1',
            'sector_2',
            'sector_3',
            'speed_trap',
            'is_pit_out_lap',
            'is_pit_in_lap',
            'is_personal_best',
        )
