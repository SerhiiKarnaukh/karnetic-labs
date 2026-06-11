from django.db.models import Q

from rest_framework.decorators import api_view

from social_posts.models import Post
from social_posts.serializers import PostSerializer
from social_profiles.models import Profile
from social_profiles.serializers import ProfileSerializer
from social_posts.views.pagination import PostPagination


@api_view(['GET', 'POST'])
def search(request):
    query = (
        request.data.get('query')
        if request.method == 'POST'
        else request.query_params.get('query')
    )
    request_user = None
    user_ids = []
    if request.user.is_authenticated:
        request_user = Profile.objects.get(user=request.user)

    profiles = Profile.objects.filter(
        Q(first_name__icontains=query) | Q(last_name__icontains=query),
    )
    profile_serializer = ProfileSerializer(
        profiles,
        context={'request': request},
        many=True,
    )

    if request_user is not None:
        user_ids.append(request_user.id)
        for user in request_user.friends.all():
            user_ids.append(user.id)

    posts = Post.objects.filter(
        Q(body__icontains=query, is_private=False)
        | Q(created_by_id__in=list(user_ids), body__icontains=query),
    )
    paginator = PostPagination()
    paginated_posts = paginator.paginate_queryset(posts, request)
    posts_serializer = PostSerializer(
        paginated_posts,
        context={'request': request},
        many=True,
    )

    return paginator.get_paginated_response({
        'profiles': profile_serializer.data,
        'posts': posts_serializer.data,
    })
