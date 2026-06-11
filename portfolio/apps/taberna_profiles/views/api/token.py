from django.contrib.auth import authenticate

from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from taberna_profiles.models import UserProfile
from taberna_profiles.utils import handle_cart_after_login


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = authenticate(
                email=request.data.get('email'),
                password=request.data.get('password')
            )
            if user is not None:
                try:
                    user_profile = UserProfile.objects.get(user=user)
                    handle_cart_after_login(request, user_profile)
                except UserProfile.DoesNotExist:
                    return Response({"error": "User profile does not exist."}, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"error": "Invalid login credentials."}, status=status.HTTP_401_UNAUTHORIZED)

            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Authentication failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
