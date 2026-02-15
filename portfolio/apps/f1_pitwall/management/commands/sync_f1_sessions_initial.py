"""One-time initial sync of F1 data for fresh deployments.

Checks if the sessions table is empty. If so, syncs 2023-2025 data
from OpenF1. If data already exists, does nothing. Designed to be
called from run.sh in the background on first deploy.
"""

import logging

from django.core.management.base import BaseCommand

from f1_pitwall.models import Session
from f1_pitwall.services.session_sync import SessionSyncService

logger = logging.getLogger(__name__)

INITIAL_SYNC_YEARS = [2023, 2024, 2025]


class Command(BaseCommand):
    help = 'Initial F1 data sync — runs only if sessions table is empty'

    def handle(self, *args, **options):
        if Session.objects.exists():
            self.stdout.write(
                "Sessions table already has data, skipping initial sync.",
            )
            return

        self.stdout.write("Empty sessions table detected. Starting initial sync...")
        service = SessionSyncService()

        for year in INITIAL_SYNC_YEARS:
            self._sync_year(service, year)

        self.stdout.write(self.style.SUCCESS("Initial F1 data sync complete."))

    def _sync_year(self, service, year):
        """Sync sessions and drivers for a single year."""
        self.stdout.write(f"  Syncing {year}...")

        session_result = service.sync_sessions(year=year)
        self.stdout.write(
            f"    Sessions: {session_result['created']} created, "
            f"{session_result['updated']} updated",
        )

        driver_result = service.sync_drivers()
        self.stdout.write(
            f"    Drivers: {driver_result['created']} created, "
            f"{driver_result['updated']} updated",
        )
