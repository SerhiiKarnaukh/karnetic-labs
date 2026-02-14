"""
Django command to collect server statistics and save to database.
Designed to run automatically on each deploy.
"""
import os
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection

from core.models import ServerStatistics

ERROR_PREFIX = ServerStatistics.ERROR_PREFIX


class Command(BaseCommand):
    """Collect server resource usage and persist a snapshot."""

    help = 'Collect server statistics (DB size, media, disk) and save to DB'

    def handle(self, *args, **options):
        stats = {
            'app_version': settings.VERSION,
            'db_size': self._get_db_size(),
            'media_size': self._get_media_size(),
            **self._get_disk_usage(),
        }

        self._log_errors(stats)
        self._save(stats)

    def _save(self, stats):
        """Persist statistics as a single record."""
        _record, created = ServerStatistics.objects.update_or_create(
            pk=1, defaults=stats,
        )
        action = 'created' if created else 'updated'
        self.stdout.write(self.style.SUCCESS(
            f'Statistics {action}: {_record}'
        ))

    def _log_errors(self, stats):
        """Warn about any metrics that failed to collect."""
        for key, value in stats.items():
            if str(value).startswith(ERROR_PREFIX):
                self.stderr.write(self.style.WARNING(
                    f'  {key}: {value}'
                ))

    def _get_db_size(self):
        """Get current database size from PostgreSQL."""
        try:
            db_name = settings.DATABASES['default']['NAME']
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_size_pretty(pg_database_size(%s));",
                    [db_name],
                )
                return cursor.fetchone()[0]
        except Exception as e:
            return f'{ERROR_PREFIX}: DB query failed ({e})'

    def _get_media_size(self):
        """Calculate total size of the media directory."""
        try:
            media_root = settings.MEDIA_ROOT
            if not os.path.exists(media_root):
                return f'{ERROR_PREFIX}: media dir not found'
            total = sum(
                os.path.getsize(os.path.join(dirpath, f))
                for dirpath, _dirnames, filenames in os.walk(media_root)
                for f in filenames
            )
            return self._human_readable_size(total)
        except Exception as e:
            return f'{ERROR_PREFIX}: media scan failed ({e})'

    def _get_disk_usage(self):
        """Get disk total, used, and available for root partition."""
        try:
            usage = shutil.disk_usage('/')
            return {
                'disk_total': self._human_readable_size(usage.total),
                'disk_used': self._human_readable_size(usage.used),
                'disk_available': self._human_readable_size(usage.free),
            }
        except Exception as e:
            msg = f'{ERROR_PREFIX}: disk info failed ({e})'
            return {
                'disk_total': msg,
                'disk_used': msg,
                'disk_available': msg,
            }

    @staticmethod
    def _human_readable_size(size_bytes):
        """Convert bytes to human-readable string."""
        for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
            if abs(size_bytes) < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"
