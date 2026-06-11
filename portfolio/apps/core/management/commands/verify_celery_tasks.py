import os
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from portfolio.celery import app as celery_app

TASK_IMPORTS = {
    'social_posts.tasks.create_social_posts_trends': (
        'social_posts.tasks', 'create_social_posts_trends',
    ),
    'social_profiles.tasks.create_social_friend_suggestions': (
        'social_profiles.tasks', 'create_social_friend_suggestions',
    ),
    'social_profiles.tasks.delete_old_rejected_friendship_requests': (
        'social_profiles.tasks', 'delete_old_rejected_friendship_requests',
    ),
    'taberna_cart.tasks.delete_old_carts': (
        'taberna_cart.tasks', 'delete_old_carts',
    ),
    'ai_lab.tasks.delete_generated_media': (
        'ai_lab.tasks', 'delete_generated_media',
    ),
}


def import_task(task_name):
    module_path, attr = TASK_IMPORTS[task_name]
    module = __import__(module_path, fromlist=[attr])
    return getattr(module, attr)


def get_worker_task_names():
    inspector = celery_app.control.inspect(timeout=5)
    registered = inspector.registered() or {}
    names = set()
    for worker_tasks in registered.values():
        names.update(worker_tasks)
    return names


def seed_task_fixtures():
    from core.utils import create_active_user
    from social_posts.models import Post, Trend
    from social_profiles.models import FriendshipRequest, Profile
    from taberna_cart.models import Cart

    user_a = create_active_user(
        email='celery-a@example.com',
        username='celery_a',
        password='pass123',
        first_name='Celery',
        last_name='Alpha',
    )
    user_b = create_active_user(
        email='celery-b@example.com',
        username='celery_b',
        password='pass123',
        first_name='Celery',
        last_name='Beta',
    )
    user_c = create_active_user(
        email='celery-c@example.com',
        username='celery_c',
        password='pass123',
        first_name='Celery',
        last_name='Gamma',
    )

    profile_a = Profile.objects.create(user=user_a)
    profile_b = Profile.objects.create(user=user_b)
    profile_c = Profile.objects.create(user=user_c)

    profile_a.friends.add(profile_b)
    profile_b.friends.add(profile_c)

    Post.objects.create(
        body='Hello #celerytest and #django',
        created_by=profile_a,
        is_private=False,
    )
    Trend.objects.create(hashtag='stale', occurences=1)

    rejected = FriendshipRequest.objects.create(
        created_by=profile_a,
        created_for=profile_c,
        status=FriendshipRequest.REJECTED,
    )
    FriendshipRequest.objects.filter(pk=rejected.pk).update(
        created_at=timezone.now() - timedelta(days=8),
    )

    Cart.objects.create(
        cart_id='old-cart-celery-test',
        date_added=(timezone.now() - timedelta(days=61)).date(),
    )

    for folder in ('generated_images', 'generated_voices', 'vision_images'):
        folder_path = os.path.join(settings.MEDIA_ROOT, folder)
        os.makedirs(folder_path, exist_ok=True)
        with open(os.path.join(folder_path, 'celery-verify.txt'), 'w', encoding='utf-8') as handle:
            handle.write('celery verify')


class Command(BaseCommand):
    help = 'Verify Celery beat tasks are registered on workers and can be executed.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Only verify imports, beat schedule, and worker registration.',
        )
        parser.add_argument(
            '--no-seed',
            action='store_true',
            help='Skip creating fixture data before task execution.',
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=60,
            help='Seconds to wait for each async task result.',
        )

    def handle(self, *args, **options):
        if not options['no_seed'] and not options['check_only']:
            self.stdout.write('Seeding fixture data for task preconditions...')
            seed_task_fixtures()

        worker_tasks = get_worker_task_names()
        if not worker_tasks:
            self.stderr.write(self.style.ERROR('No Celery workers responded to inspect.'))
            return

        beat_entries = celery_app.conf.beat_schedule
        failures = 0

        for beat_key, entry in beat_entries.items():
            task_name = entry['task']
            self.stdout.write(f'\n[{beat_key}] {task_name}')

            if task_name not in worker_tasks:
                self.stderr.write(self.style.ERROR('  NOT registered on worker'))
                failures += 1
                continue

            self.stdout.write(self.style.SUCCESS('  registered on worker'))

            try:
                task = import_task(task_name)
            except (ImportError, AttributeError, KeyError) as exc:
                self.stderr.write(self.style.ERROR(f'  import failed: {exc}'))
                failures += 1
                continue

            self.stdout.write(self.style.SUCCESS('  importable from public tasks package'))

            if options['check_only']:
                continue

            result = task.delay()
            self.stdout.write(f'  dispatched: {result.id}')
            try:
                result.get(timeout=options['timeout'])
                self.stdout.write(self.style.SUCCESS('  completed'))
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f'  execution failed: {exc}'))
                failures += 1

        if failures:
            self.stderr.write(self.style.ERROR(f'\n{failures} task(s) failed verification.'))
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS('\nAll Celery beat tasks verified successfully.'))
