from rest_framework.decorators import api_view

from social_posts.models import Post
from social_posts.serializers import PostSerializer
from social_profiles.models import FriendshipRequest, Profile
from social_profiles.serializers import ProfileSerializer
from social_posts.views.pagination import PostPagination


@api_view(['GET'])
def post_list_profile(request, slug):
    profile = Profile.objects.get(slug=slug)
    request_user = None
    if request.user.is_authenticated:
        request_user = Profile.objects.get(user=request.user)
    created_by_id = profile.id
    posts = Post.objects.filter(created_by_id=created_by_id)

    if request_user is not None:
        if (request_user not in profile.friends.all()
                and request_user.id != profile.id):
            posts = posts.filter(is_private=False)

        can_send_friendship_request = True
        if request_user in profile.friends.all():
            can_send_friendship_request = False

        check1 = FriendshipRequest.objects.filter(
            created_for=request_user,
        ).filter(created_by=profile)
        check2 = FriendshipRequest.objects.filter(
            created_for=profile,
        ).filter(created_by=request_user)

        if check1.exists() or check2.exists():
            can_send_friendship_request = False
            if check1.exists() and check1.first().status == 'rejected':
                can_send_friendship_request = 'rejected'
            if check2.exists() and check2.first().status == 'rejected':
                can_send_friendship_request = 'rejected'
    else:
        can_send_friendship_request = False
        posts = posts.filter(is_private=False)

    paginator = PostPagination()
    paginated_posts = paginator.paginate_queryset(posts, request)
    posts_serializer = PostSerializer(
        paginated_posts,
        context={'request': request},
        many=True,
    )

    profile_serializer = ProfileSerializer(
        profile,
        context={'request': request},
    )

    return paginator.get_paginated_response({
        'posts': posts_serializer.data,
        'profile': profile_serializer.data,
        'can_send_friendship_request': can_send_friendship_request,
    })
