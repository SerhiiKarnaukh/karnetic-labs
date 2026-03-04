"""Serializers for strategy calculation input/output."""

from rest_framework import serializers

from f1_pitwall.constants import COMPOUND_CHOICES


class StrategyCalculateRequestSerializer(serializers.Serializer):
    """Validate strategy calculation request payload."""

    current_lap = serializers.IntegerField(min_value=1)
    total_laps = serializers.IntegerField(min_value=1)
    current_compound = serializers.ChoiceField(
        choices=[choice[0] for choice in COMPOUND_CHOICES],
    )
    tyre_age = serializers.IntegerField(min_value=0)
    base_lap_time = serializers.FloatField(min_value=0.1)
    weather_forecast = serializers.DictField(required=False, default=dict)
    gap_ahead = serializers.FloatField()
    gap_behind = serializers.FloatField()

    def validate(self, attrs):
        if attrs['current_lap'] > attrs['total_laps']:
            raise serializers.ValidationError(
                {'current_lap': 'current_lap cannot exceed total_laps.'},
            )
        return attrs


class StrategyStopSerializer(serializers.Serializer):
    """Serialize strategy pit stop metadata."""

    lap = serializers.IntegerField()
    compound = serializers.CharField()


class StrategyOptionSerializer(serializers.Serializer):
    """Serialize one strategy option from StrategyEngine."""

    name = serializers.CharField()
    total_time = serializers.FloatField()
    pit_stops = StrategyStopSerializer(many=True)
    tire_risk = serializers.FloatField()
    weather_risk = serializers.FloatField()
    undercut_potential = serializers.FloatField()
    overcut_potential = serializers.FloatField()
    notes = serializers.CharField()
    score = serializers.FloatField()
