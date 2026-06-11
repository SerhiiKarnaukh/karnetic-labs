from rest_framework.decorators import api_view

from social_posts.serializers import PostSerializer
from social_posts.utils import get_trending_posts, get_user_feed_posts
from social_posts.views.pagination import PostPagination


@api_view(['GET'])
def post_list(request):
    trend = request.GET.get('trend', '').lower()

    if trend:
        posts = get_trending_posts(trend)
    else:
        posts = get_user_feed_posts(request.user)

    paginator = PostPagination()
    paginated_posts = paginator.paginate_queryset(posts, request)
    posts_serializer = PostSerializer(
        paginated_posts,
        context={'request': request},
        many=True,
    )

    return paginator.get_paginated_response({
        'posts': posts_serializer.data,
    })
