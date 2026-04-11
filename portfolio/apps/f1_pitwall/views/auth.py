"""Auth endpoints for F1 Pit Wall user onboarding."""

from django.contrib.auth import authenticate

from accounts.models import Account
from accounts.serializers import ProfileCreateSerializer
from accounts.utils import send_activation_email
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from f1_pitwall.models import F1UserProfile


class F1RegisterView(generics.CreateAPIView):
    """Register account, send activation email, and create F1UserProfile.

    If the email is already taken but that account has no F1UserProfile yet,
    only the F1 profile row is created and the response indicates that.
    """

    serializer_class = ProfileCreateSerializer

    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            user_id = response.data.get('id')
            existing_user = Account.objects.get(id=user_id)

            send_activation_email(existing_user, request)
            self._create_f1_profile(existing_user)

            return response

        except Exception as exc:
            error_message = str(exc)
            if 'unique' in error_message and 'email' in error_message:
                email = self.request.data.get('email')
                existing_user = Account.objects.filter(email=email).first()
                if existing_user:
                    if not F1UserProfile.objects.filter(user=existing_user).exists():
                        self._create_f1_profile(existing_user)
                        return Response(
                            {'detail': 'f1_profile_created'},
                            status=status.HTTP_200_OK,
                        )

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            return Response(
                serializer.data,
                status=status.HTTP_400_BAD_REQUEST,
            )

    def _create_f1_profile(self, user):
        F1UserProfile.objects.create(
            user=user,
            role=F1UserProfile.Role.VIEWER,
        )


class F1TokenObtainPairView(TokenObtainPairView):
    """JWT login for F1: Account must have an F1UserProfile row."""

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
                    F1UserProfile.objects.get(user=user)
                except F1UserProfile.DoesNotExist:
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


class F1MeView(APIView):
    """Return the authenticated user and F1 role, or 404 if F1UserProfile is missing."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = F1UserProfile.objects.get(user=request.user)
        except F1UserProfile.DoesNotExist:
            return Response(
                {'message': 'Profile does not exist for this user'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({
            'id': request.user.id,
            'email': request.user.email,
            'username': request.user.username,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'role': profile.role,
        })
