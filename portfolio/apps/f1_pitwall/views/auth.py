"""Auth endpoints for F1 Pit Wall user onboarding."""

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import ProfileCreateSerializer
from accounts.utils import send_activation_email
from f1_pitwall.models import F1UserProfile


class F1RegisterView(generics.CreateAPIView):
    """Register account, send activation email, and create F1 profile."""

    serializer_class = ProfileCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        F1UserProfile.objects.get_or_create(
            user=user,
            defaults={'role': F1UserProfile.Role.VIEWER},
        )
        send_activation_email(user, request)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)


class F1MeView(APIView):
    """Return current user with F1 role information."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = F1UserProfile.objects.get_or_create(
            user=request.user,
            defaults={'role': F1UserProfile.Role.VIEWER},
        )
        return Response({
            'id': request.user.id,
            'email': request.user.email,
            'username': request.user.username,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'role': profile.role,
        })
