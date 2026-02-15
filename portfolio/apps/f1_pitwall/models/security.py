"""Security models - APIAuditLog and ThreatEvent for security monitoring."""

import uuid

from django.conf import settings
from django.db import models

from f1_pitwall.constants import (
    SEVERITY_CHOICES,
    THREAT_TYPE_CHOICES,
)


class APIAuditLog(models.Model):
    """Records every API request to the F1 module for security auditing."""

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='f1_audit_logs',
        help_text="Null for anonymous requests",
    )
    method = models.CharField(
        max_length=10, help_text='e.g. "GET", "POST", "WS"',
    )
    path = models.CharField(max_length=500)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    status_code = models.IntegerField()
    response_time_ms = models.FloatField()
    request_body_hash = models.CharField(
        max_length=64, blank=True,
        help_text="SHA-256 hash, not the actual body",
    )
    is_suspicious = models.BooleanField(default=False, db_index=True)
    threat_indicators = models.JSONField(
        default=list, blank=True,
    )

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(
                fields=['ip_address', 'timestamp'],
                name='idx_audit_ip_timestamp',
            ),
            models.Index(
                fields=['is_suspicious', 'timestamp'],
                name='idx_audit_suspicious_ts',
            ),
        ]

    def __str__(self):
        suspicious = " [!]" if self.is_suspicious else ""
        return (
            f"{self.method} {self.path} "
            f"({self.status_code}){suspicious}"
        )


class ThreatEvent(models.Model):
    """A detected security threat from the Threat Monitor analysis."""

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    threat_type = models.CharField(
        max_length=30, choices=THREAT_TYPE_CHOICES,
    )
    severity = models.CharField(
        max_length=10, choices=SEVERITY_CHOICES,
    )
    source_ip = models.GenericIPAddressField()
    description = models.TextField()
    raw_request = models.JSONField(
        help_text="Sanitized request data, no sensitive information",
    )
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        resolved = " [resolved]" if self.is_resolved else ""
        return (
            f"[{self.severity}] {self.threat_type} "
            f"from {self.source_ip}{resolved}"
        )
