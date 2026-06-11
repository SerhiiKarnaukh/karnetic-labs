from rest_framework import generics, status
from rest_framework.response import Response

from accounts.models import Account
from accounts.serializers import ProfileCreateSerializer
from accounts.utils import send_activation_email
from taberna_profiles.models import UserProfile


class TabernaProfileCreateView(generics.CreateAPIView):
    serializer_class = ProfileCreateSerializer

    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            user_id = response.data.get('id')
            existing_user = Account.objects.get(id=user_id)

            send_activation_email(existing_user, request)

            self.create_profile(existing_user)

            return response

        except Exception as e:

            error_message = str(e)
            if 'unique' in error_message and 'email' in error_message:
                email = self.request.data.get('email')
                existing_user = Account.objects.filter(email=email).first()
                if existing_user:
                    if not hasattr(existing_user, 'userprofile'):
                        self.create_profile(existing_user)
                        return Response({"detail": "taberna_profile_created"},
                                        status=status.HTTP_200_OK)

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data,
                            status=status.HTTP_400_BAD_REQUEST)

    def create_profile(self, user):
        UserProfile.objects.create(user=user)
