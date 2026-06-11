from django.http import JsonResponse

from rest_framework.decorators import api_view

from social_notification.models import Notification
from social_profiles.models import Profile


@api_view(['POST'])
def read_notification(request, pk):
    request_user = Profile.objects.get(user=request.user)

    notification = Notification.objects.filter(
        created_for=request_user,
    ).get(pk=pk)
    notification.is_read = True
    notification.save()

    return JsonResponse({'message': 'notification read'})
