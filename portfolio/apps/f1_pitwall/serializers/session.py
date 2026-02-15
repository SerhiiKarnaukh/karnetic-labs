"""Serializers for the Session model."""

from rest_framework import serializers

from f1_pitwall.models import Session


class SessionListSerializer(serializers.ModelSerializer):
    """Compact session representation for list endpoints."""

    class Meta:
        model = Session
        fields = (
            'id',
            'session_key',
            'session_name',
            'session_type',
            'circuit_short_name',
            'country_name',
            'country_code',
            'date_start',
            'year',
            'is_live',
        )


class SessionDetailSerializer(serializers.ModelSerializer):
    """Full session representation for detail endpoints."""

    class Meta:
        model = Session
        fields = (
            'id',
            'session_key',
            'meeting_key',
            'session_name',
            'session_type',
            'circuit_name',
            'circuit_short_name',
            'country_name',
            'country_code',
            'date_start',
            'date_end',
            'year',
            'is_live',
            'created_at',
            'updated_at',
        )
