from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse

from rest_framework.decorators import api_view
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .forms import ProfileForm

from .models import Profile, FriendshipRequest
from accounts.models import Account

from .serializers import ProfileSerializer, FriendshipRequestSerializer
from accounts.serializers import ProfileCreateSerializer

from accounts.utils import send_activation_email
from social_notification.utils import create_notification


class SocialProfileCreateView(generics.CreateAPIView):
    serializer_class = ProfileCreateSerializer

    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            user_id = response.data.get('id')
            existing_user = Account.objects.get(id=user_id)

            # send activation email
            send_activation_email(existing_user, request)

            self.create_profile(existing_user)

            return response

        except Exception as e:

            error_message = str(e)
            if 'unique' in error_message and 'email' in error_message:
                email = self.request.data.get('email')
                existing_user = Account.objects.filter(email=email).first()
                if existing_user:
                    if not hasattr(existing_user, 'profile'):
                        self.create_profile(existing_user)
                        return Response({"detail": "social_profile_created"},
                                        status=status.HTTP_200_OK)

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data,
                            status=status.HTTP_400_BAD_REQUEST)

    def create_profile(self, user):
        Profile.objects.create(
            user=user,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
            email=user.email,
        )


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
            data={'message': 'Profile does not exist for this user'})


@api_view(['GET'])
def friends(request, slug):
    user = Profile.objects.get(slug=slug)
    request_user = Profile.objects.get(user=request.user)
    requests = []

    if user == request_user:
        requests = FriendshipRequest.objects.filter(
            created_for=request_user, status=FriendshipRequest.SENT)
        requests = FriendshipRequestSerializer(requests,
                                               context={'request': request},
                                               many=True)
        requests = requests.data

    friends = user.friends.all()

    return JsonResponse(
        {
            'user':
            ProfileSerializer(user, context={
                'request': request
            }).data,
            'friends':
            ProfileSerializer(friends, context={
                'request': request
            }, many=True).data,
            'requests':
            requests
        },
        safe=False)


@api_view(['POST'])
def send_friendship_request(request, slug):
    user = Profile.objects.get(slug=slug)
    request_user = Profile.objects.get(user=request.user)

    check1 = FriendshipRequest.objects.filter(created_for=request_user).filter(
        created_by=user)
    check2 = FriendshipRequest.objects.filter(created_for=user).filter(
        created_by=request_user)

    if not check1 or not check2:
        friend_request = FriendshipRequest.objects.create(created_for=user,
                                                          created_by=request_user)

        create_notification(request, 'new_friendrequest', friendrequest_id=friend_request.id)

        return JsonResponse({'message': 'friendship request created'})
    else:
        return JsonResponse({'message': 'request already sent'})


@api_view(['POST'])
def handle_request(request, slug, status):
    user = Profile.objects.get(slug=slug)
    request_user = Profile.objects.get(user=request.user)
    friendship_request = FriendshipRequest.objects.filter(
        created_for=request_user).get(created_by=user)
    friendship_request.status = status
    friendship_request.save()

    if status == 'accepted':
        user.friends.add(request_user)
        user.friends_count = user.friends_count + 1
        user.save()
        request_user.friends_count = request_user.friends_count + 1
        request_user.save()

        create_notification(request, 'accepted_friendrequest', friendrequest_id=friendship_request.id)
    elif status == 'rejected':
        create_notification(request, 'rejected_friendrequest', friendrequest_id=friendship_request.id)

    return JsonResponse({'message': 'friendship request updated'})


@api_view(['GET'])
def my_friendship_suggestions(request):
    pass
    request_user = Profile.objects.get(user=request.user)
    serializer = ProfileSerializer(request_user.people_you_may_know.all(), many=True, context={
        'request': request
    })

    return JsonResponse(serializer.data, safe=False)


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


class SocialTokenObtainPairView(TokenObtainPairView):
    """JWT login for Social: Account must have a Profile row."""

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = authenticate(
                email=request.data.get('email'),
                password=request.data.get('password'),
            )
            if user is not None:
                try:
                    Profile.objects.get(user=user)
                except Profile.DoesNotExist:
                    return Response(
                        {'error': 'User profile does not exist.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                return Response(
                    {'error': 'Invalid login credentials.'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response(
                {'error': f'Authentication failed: {exc}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
