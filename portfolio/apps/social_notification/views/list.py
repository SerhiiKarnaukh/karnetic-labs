from django.http import JsonResponse

from rest_framework.decorators import api_view

from social_notification.serializers import NotificationSerializer
from social_profiles.models import Profile


@api_view(['GET'])
def notifications(request):
    request_user = Profile.objects.get(user=request.user)

    received_notifications = request_user.received_notifications.filter(
        is_read=False,
    )
    serializer = NotificationSerializer(received_notifications, many=True)

    return JsonResponse(serializer.data, safe=False)
