"""Management command for manually syncing F1 session data from OpenF1."""

from django.core.management.base import BaseCommand

from f1_pitwall.services.session_sync import SessionSyncService


class Command(BaseCommand):
    help = 'Sync F1 session and driver data from OpenF1 API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year', type=int, default=None,
            help='Filter sessions by year (e.g. --year 2025)',
        )

    def handle(self, *args, **options):
        year = options['year']
        service = SessionSyncService()

        self.stdout.write(f"Syncing sessions{f' for {year}' if year else ''}...")
        session_result = service.sync_sessions(year=year)
        self._print_result('Sessions', session_result)

        self.stdout.write("Syncing drivers...")
        driver_result = service.sync_drivers()
        self._print_result('Drivers', driver_result)

        self.stdout.write(self.style.SUCCESS('Sync complete.'))

    def _print_result(self, label, result):
        self.stdout.write(
            f"  {label}: {result['created']} created, "
            f"{result['updated']} updated"
        )
