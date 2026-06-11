from collections import Counter
import re
from datetime import timedelta

from celery import shared_task
from django.db.models import Q
from django.utils import timezone

from social_posts.models import Post, Trend


@shared_task(name='social_posts.tasks.create_social_posts_trends')
def create_social_posts_trends():
    this_hour = timezone.now().replace(minute=0, second=0, microsecond=0)
    twenty_four_hours = this_hour - timedelta(hours=24)

    Trend.objects.all().delete()

    posts = Post.objects.filter(created_at__gte=twenty_four_hours, is_private=False)

    if not posts.exists():
        posts = Post.objects.filter(is_private=False).order_by('-created_at')[:5]

    trends_counter = Counter()

    for post in posts:
        for word in post.body.split():
            if len(word) > 1 and word[0] == '#':
                hashtag = word[1:].lower()
                hashtag = re.sub(r'\W+$', '', hashtag)
                hashtag_pattern = r'#' + re.escape(hashtag) + r'(\b|[^a-zA-Z0-9_])'

                occurences = Post.objects.filter(
                    Q(is_private=False) & Q(body__iregex=hashtag_pattern),
                ).count()

                trends_counter[hashtag] = occurences

    for hashtag, occurences in trends_counter.most_common(10):
        Trend.objects.create(hashtag=hashtag, occurences=occurences)
