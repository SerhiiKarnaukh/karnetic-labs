from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from social_profiles.forms import ProfileForm
from social_profiles.models import Profile
from social_profiles.serializers import ProfileSerializer


@api_view(['GET'])
def me(request):
    user = request.user
    try:
        profile = Profile.objects.get(user=user)
        serializer = ProfileSerializer(profile, context={'request': request})
        response_data = serializer.data
        return Response(response_data)
    except Profile.DoesNotExist:
        return Response(
            status=status.HTTP_404_NOT_FOUND,
            data={'message': 'Profile does not exist for this user'},
        )


@api_view(['POST'])
def editprofile(request):
    user = request.user
    email = request.data.get('email')
    username = request.data.get('username')

    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        profile = None

    if Profile.objects.exclude(id=profile.id).filter(email=email).exists():
        return JsonResponse({'message': 'Email already exists!'})
    elif Profile.objects.exclude(id=profile.id).filter(
            username=username).exists():
        return JsonResponse({'message': 'Username already exists!'})
    else:
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            new_profile = form.save()
            new_avatar_url = None
            if new_profile.avatar:
                new_avatar_url = request.build_absolute_uri(
                    new_profile.avatar.url)
            return JsonResponse({
                'message': 'Information updated successfully',
                'new_slug': new_profile.slug,
                'new_avatar': new_avatar_url,
            })

        return JsonResponse({'message': 'Invalid form data!'})


@api_view(['POST'])
def editpassword(request):
    user = request.user

    form = PasswordChangeForm(data=request.POST, user=user)

    if form.is_valid():
        form.save()

        return JsonResponse({'message': 'success'})
    else:
        return JsonResponse({'message': form.errors.as_json()}, safe=False)
