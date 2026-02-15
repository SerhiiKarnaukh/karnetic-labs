from celery import Celery
import os
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio.settings')

app = Celery('portfolio')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'create_social_posts_trends': {
        'task': 'social_posts.tasks.create_social_posts_trends',
        'schedule': crontab(hour=4, minute=0),
        'options': {'timezone': 'Europe/Kiev'},
    },
    'create_social_friend_suggestions': {
        'task': 'social_profiles.tasks.create_social_friend_suggestions',
        'schedule': crontab(hour=5, minute=0),
        'options': {'timezone': 'Europe/Kiev'},
    },
    'delete-old-rejected-friendship-requests': {
        'task': 'social_profiles.tasks.delete_old_rejected_friendship_requests',
        'schedule': crontab(hour=4, minute=30),
        'options': {'timezone': 'Europe/Kiev'},
    },
    'delete_old_carts': {
        'task': 'taberna_cart.tasks.delete_old_carts',
        'schedule': crontab(hour=3, minute=0),
        'options': {'timezone': 'Europe/Kiev'},
    },
    'delete_generated_media': {
        'task': 'ai_lab.tasks.delete_generated_media',
        'schedule': crontab(hour=2, minute=0),
        'options': {'timezone': 'Europe/Kiev'},
    },
    'sync_f1_sessions': {
        'task': 'f1_pitwall.tasks.sync_sessions.sync_f1_sessions',
        'schedule': crontab(minute=0, hour='*/6'),
    },
}
