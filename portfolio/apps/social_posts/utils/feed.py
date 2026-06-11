import re

from social_posts.models import Post
from social_profiles.models import Profile


def get_trending_posts(trend: str):
    hashtag_pattern = r'#' + re.escape(trend) + r'(?![a-zA-Z0-9_])'
    return Post.objects.filter(
        is_private=False,
        body__iregex=hashtag_pattern,
    )


def get_user_feed_posts(user):
    if not user.is_authenticated:
        return Post.objects.filter(is_private=False)

    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        return Post.objects.filter(is_private=False)

    friend_ids = profile.friends.values_list('id', flat=True)
    user_ids = [profile.id] + list(friend_ids)

    return Post.objects.filter(created_by_id__in=user_ids)
