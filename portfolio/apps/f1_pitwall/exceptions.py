"""Custom exception classes for the F1 Pit Wall module."""


class F1PitwallError(Exception):
    """Base exception for all F1 Pit Wall errors."""


class OpenF1APIError(F1PitwallError):
    """Raised when the OpenF1 API returns an unexpected response."""


class OpenF1ConnectionError(F1PitwallError):
    """Raised when connection to the OpenF1 API fails."""


class SessionNotFoundError(F1PitwallError):
    """Raised when a requested F1 session does not exist."""


class TelemetryStreamError(F1PitwallError):
    """Raised when the telemetry streaming loop encounters an error."""


class StrategyCalculationError(F1PitwallError):
    """Raised when strategy calculation fails due to invalid input."""


class SecurityThreatDetected(F1PitwallError):
    """Raised when a security threat is detected by the API Shield."""

    def __init__(self, threat_type, severity, description=''):
        self.threat_type = threat_type
        self.severity = severity
        self.description = description
        super().__init__(f'{severity} threat: {threat_type} - {description}')
