from django.http import JsonResponse

from rest_framework.decorators import api_view

from social_posts.forms import AttachmentForm, PostForm
from social_posts.serializers import PostSerializer
from social_profiles.models import Profile


@api_view(['POST'])
def post_create(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    form = PostForm(request.POST)
    user = request.user
    profile = Profile.objects.get(user=user)

    images = [
        value for key, value in request.FILES.items()
        if key.startswith('images')
    ]

    attachments = []

    for image in images:
        attachment_form = AttachmentForm(data=None, files={'image': image})
        if attachment_form.is_valid():
            attachment = attachment_form.save(commit=False)
            attachment.created_by = profile
            attachment.save()
            attachments.append(attachment)

    if form.is_valid():
        post = form.save(commit=False)
        post.created_by = profile
        post.save()

        if attachments:
            for attachment in attachments:
                post.attachments.add(attachment)

        profile.posts_count = profile.posts_count + 1
        profile.save()

        serializer = PostSerializer(post, context={'request': request})

        return JsonResponse(serializer.data, safe=False)
    else:
        return JsonResponse({'error': 'Form is not valid'}, status=400)
