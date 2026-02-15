"""Admin site registration for all F1 Pit Wall models."""

from django.contrib import admin

from f1_pitwall.models import (
    APIAuditLog,
    Driver,
    LapData,
    PitStop,
    RaceControlMessage,
    Session,
    Stint,
    TelemetrySnapshot,
    ThreatEvent,
    WeatherData,
)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = (
        'session_key', 'session_name', 'session_type',
        'circuit_short_name', 'country_name', 'year',
        'date_start', 'is_live',
    )
    list_filter = ('year', 'session_type', 'is_live', 'country_name')
    search_fields = ('circuit_name', 'circuit_short_name', 'country_name')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = (
        'driver_number', 'full_name', 'name_acronym',
        'team_name', 'country_code', 'is_active',
    )
    list_filter = ('team_name', 'is_active')
    search_fields = ('full_name', 'name_acronym', 'team_name')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(TelemetrySnapshot)
class TelemetrySnapshotAdmin(admin.ModelAdmin):
    list_display = (
        'timestamp', 'driver', 'session',
        'speed', 'rpm', 'gear', 'throttle', 'brake', 'drs',
    )
    list_filter = ('session', 'driver')
    search_fields = ('driver__full_name', 'driver__name_acronym')
    readonly_fields = ('id', 'created_at')
    raw_id_fields = ('session', 'driver')


@admin.register(LapData)
class LapDataAdmin(admin.ModelAdmin):
    list_display = (
        'session', 'driver', 'lap_number', 'lap_duration',
        'sector_1', 'sector_2', 'sector_3',
        'is_pit_in_lap', 'is_pit_out_lap', 'is_personal_best',
    )
    list_filter = (
        'session', 'is_pit_in_lap', 'is_pit_out_lap', 'is_personal_best',
    )
    search_fields = ('driver__full_name', 'driver__name_acronym')
    readonly_fields = ('id', 'created_at')
    raw_id_fields = ('session', 'driver')


@admin.register(PitStop)
class PitStopAdmin(admin.ModelAdmin):
    list_display = (
        'session', 'driver', 'lap_number',
        'pit_duration', 'timestamp',
    )
    list_filter = ('session',)
    search_fields = ('driver__full_name', 'driver__name_acronym')
    readonly_fields = ('id', 'created_at')
    raw_id_fields = ('session', 'driver')


@admin.register(Stint)
class StintAdmin(admin.ModelAdmin):
    list_display = (
        'session', 'driver', 'stint_number', 'compound',
        'tyre_age_at_start', 'lap_start', 'lap_end',
    )
    list_filter = ('session', 'compound')
    search_fields = ('driver__full_name', 'driver__name_acronym')
    readonly_fields = ('id', 'created_at')
    raw_id_fields = ('session', 'driver')


@admin.register(WeatherData)
class WeatherDataAdmin(admin.ModelAdmin):
    list_display = (
        'session', 'timestamp', 'air_temperature',
        'track_temperature', 'humidity', 'wind_speed', 'rainfall',
    )
    list_filter = ('session', 'rainfall')
    readonly_fields = ('id', 'created_at')
    raw_id_fields = ('session',)


@admin.register(RaceControlMessage)
class RaceControlMessageAdmin(admin.ModelAdmin):
    list_display = (
        'session', 'timestamp', 'category', 'flag',
        'driver_number', 'lap_number', 'message_preview',
    )
    list_filter = ('session', 'category', 'flag')
    search_fields = ('message',)
    readonly_fields = ('id', 'created_at')
    raw_id_fields = ('session',)

    @admin.display(description='Message')
    def message_preview(self, obj):
        return obj.message[:80] if obj.message else ''


@admin.register(APIAuditLog)
class APIAuditLogAdmin(admin.ModelAdmin):
    list_display = (
        'timestamp', 'method', 'path', 'ip_address',
        'status_code', 'response_time_ms', 'is_suspicious',
    )
    list_filter = ('method', 'is_suspicious', 'status_code')
    search_fields = ('path', 'ip_address', 'user_agent')
    readonly_fields = ('id', 'timestamp')
    raw_id_fields = ('user',)


@admin.register(ThreatEvent)
class ThreatEventAdmin(admin.ModelAdmin):
    list_display = (
        'timestamp', 'threat_type', 'severity',
        'source_ip', 'is_resolved', 'resolved_at',
    )
    list_filter = ('threat_type', 'severity', 'is_resolved')
    search_fields = ('source_ip', 'description')
    readonly_fields = ('id', 'timestamp')
