import os

from django.http import JsonResponse

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from social_notification.utils import create_notification
from social_posts.models import Like, Post
from social_profiles.models import Profile


@api_view(['POST'])
def post_like(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    post = Post.objects.get(pk=pk)
    request_user = Profile.objects.get(user=request.user)

    if not post.likes.filter(created_by=request_user):
        like = Like.objects.create(created_by=request_user)

        post = Post.objects.get(pk=pk)
        post.likes_count = post.likes_count + 1
        post.likes.add(like)
        post.save()

        if post.created_by != request_user:
            create_notification(request, 'post_like', post_id=post.id)

        return JsonResponse({'message': 'like created'})
    else:
        return JsonResponse({'message': 'post already liked'})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def post_delete(request, pk):
    request_user = Profile.objects.get(user=request.user)

    try:
        post = Post.objects.filter(created_by=request_user).get(pk=pk)
    except Post.DoesNotExist:
        return JsonResponse({'detail': 'Not found.'}, status=404)

    for attachment in post.attachments.all():
        if attachment.image:
            if os.path.isfile(attachment.image.path):
                os.remove(attachment.image.path)
        attachment.delete()
    post.delete()

    request_user.posts_count = request_user.posts_count - 1
    request_user.save()

    return JsonResponse({'message': 'post deleted'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_report(request, pk):
    request_user = Profile.objects.get(user=request.user)
    post = Post.objects.get(pk=pk)
    post.reported_by_users.add(request_user)
    post.save()

    return JsonResponse({'message': 'post reported'})
