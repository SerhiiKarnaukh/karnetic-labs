from django.db import models


class ServerStatistics(models.Model):
    """Snapshot of server resource usage collected on each deploy."""

    ERROR_PREFIX = 'N/A'

    collected_at = models.DateTimeField(auto_now_add=True)
    app_version = models.CharField(max_length=20)
    db_size = models.CharField(max_length=50)
    media_size = models.CharField(max_length=50)
    disk_total = models.CharField(max_length=50)
    disk_used = models.CharField(max_length=50)
    disk_available = models.CharField(max_length=50)

    class Meta:
        ordering = ['-collected_at']
        verbose_name = 'Server Statistics'
        verbose_name_plural = 'Server Statistics'

    def __str__(self):
        return f"v{self.app_version} — {self.collected_at:%Y-%m-%d %H:%M}"
