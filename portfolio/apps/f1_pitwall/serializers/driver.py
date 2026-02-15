"""Serializers for the Driver model."""

from rest_framework import serializers

from f1_pitwall.models import Driver


class DriverListSerializer(serializers.ModelSerializer):
    """Compact driver representation for list endpoints."""

    class Meta:
        model = Driver
        fields = (
            'driver_number',
            'full_name',
            'name_acronym',
            'team_name',
            'team_colour',
            'country_code',
            'is_active',
        )


class DriverDetailSerializer(serializers.ModelSerializer):
    """Full driver representation for detail endpoints."""

    class Meta:
        model = Driver
        fields = (
            'id',
            'driver_number',
            'full_name',
            'name_acronym',
            'team_name',
            'team_colour',
            'headshot_url',
            'country_code',
            'is_active',
            'created_at',
            'updated_at',
        )
