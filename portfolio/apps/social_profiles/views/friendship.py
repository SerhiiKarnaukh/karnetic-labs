from django.http import JsonResponse

from rest_framework.decorators import api_view

from social_notification.utils import create_notification
from social_profiles.models import FriendshipRequest, Profile
from social_profiles.serializers import (
    FriendshipRequestSerializer,
    ProfileSerializer,
)


@api_view(['GET'])
def friends(request, slug):
    user = Profile.objects.get(slug=slug)
    request_user = Profile.objects.get(user=request.user)
    requests = []

    if user == request_user:
        requests = FriendshipRequest.objects.filter(
            created_for=request_user,
            status=FriendshipRequest.SENT,
        )
        requests = FriendshipRequestSerializer(
            requests,
            context={'request': request},
            many=True,
        )
        requests = requests.data

    friends = user.friends.all()

    return JsonResponse(
        {
            'user': ProfileSerializer(
                user,
                context={'request': request},
            ).data,
            'friends': ProfileSerializer(
                friends,
                context={'request': request},
                many=True,
            ).data,
            'requests': requests,
        },
        safe=False,
    )


@api_view(['POST'])
def send_friendship_request(request, slug):
    user = Profile.objects.get(slug=slug)
    request_user = Profile.objects.get(user=request.user)

    check1 = FriendshipRequest.objects.filter(
        created_for=request_user,
    ).filter(created_by=user)
    check2 = FriendshipRequest.objects.filter(created_for=user).filter(
        created_by=request_user,
    )

    if not check1 or not check2:
        friend_request = FriendshipRequest.objects.create(
            created_for=user,
            created_by=request_user,
        )

        create_notification(
            request,
            'new_friendrequest',
            friendrequest_id=friend_request.id,
        )

        return JsonResponse({'message': 'friendship request created'})
    else:
        return JsonResponse({'message': 'request already sent'})


@api_view(['POST'])
def handle_request(request, slug, status):
    user = Profile.objects.get(slug=slug)
    request_user = Profile.objects.get(user=request.user)
    friendship_request = FriendshipRequest.objects.filter(
        created_for=request_user,
    ).get(created_by=user)
    friendship_request.status = status
    friendship_request.save()

    if status == 'accepted':
        user.friends.add(request_user)
        user.friends_count = user.friends_count + 1
        user.save()
        request_user.friends_count = request_user.friends_count + 1
        request_user.save()

        create_notification(
            request,
            'accepted_friendrequest',
            friendrequest_id=friendship_request.id,
        )
    elif status == 'rejected':
        create_notification(
            request,
            'rejected_friendrequest',
            friendrequest_id=friendship_request.id,
        )

    return JsonResponse({'message': 'friendship request updated'})


@api_view(['GET'])
def my_friendship_suggestions(request):
    pass
    request_user = Profile.objects.get(user=request.user)
    serializer = ProfileSerializer(
        request_user.people_you_may_know.all(),
        many=True,
        context={'request': request},
    )

    return JsonResponse(serializer.data, safe=False)
