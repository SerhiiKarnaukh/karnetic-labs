from django.db.models import Q

from rest_framework.decorators import api_view
from rest_framework.response import Response

from social_posts.models import Post
from social_posts.serializers import PostDetailSerializer
from social_profiles.models import Profile


@api_view(['GET'])
def post_detail(request, pk):
    request_user = None
    user_ids = []
    if request.user.is_authenticated:
        request_user = Profile.objects.get(user=request.user)

    if request_user is not None:
        user_ids.append(request_user.id)
        for user in request_user.friends.all():
            user_ids.append(user.id)

    post = Post.objects.filter(
        Q(created_by_id__in=list(user_ids)) | Q(is_private=False),
    ).get(pk=pk)

    return Response({
        'post': PostDetailSerializer(post, context={'request': request}).data,
    })
