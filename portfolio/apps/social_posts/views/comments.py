from django.http import JsonResponse

from rest_framework.decorators import api_view

from social_notification.utils import create_notification
from social_posts.models import Comment, Post
from social_posts.serializers import CommentSerializer
from social_profiles.models import Profile


@api_view(['POST'])
def post_create_comment(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    request_user = Profile.objects.get(user=request.user)
    comment = Comment.objects.create(
        body=request.data.get('body'),
        created_by=request_user,
    )

    post = Post.objects.get(pk=pk)
    post.comments.add(comment)
    post.comments_count = post.comments_count + 1
    post.save()

    create_notification(request, 'post_comment', post_id=post.id)

    serializer = CommentSerializer(comment, context={'request': request})

    return JsonResponse(serializer.data, safe=False)
