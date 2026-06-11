from social_posts.views.actions import post_delete, post_like, post_report
from social_posts.views.comments import post_create_comment
from social_posts.views.create import post_create
from social_posts.views.detail import post_detail
from social_posts.views.feed import post_list
from social_posts.views.profile_feed import post_list_profile
from social_posts.views.search import search
from social_posts.views.trends import get_trends

__all__ = [
    'get_trends',
    'post_create',
    'post_create_comment',
    'post_delete',
    'post_detail',
    'post_like',
    'post_list',
    'post_list_profile',
    'post_report',
    'search',
]
