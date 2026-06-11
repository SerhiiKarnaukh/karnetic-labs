from django.contrib.auth import authenticate

from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from social_profiles.models import Profile


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
