from django.http import JsonResponse

from rest_framework.decorators import api_view

from social_posts.models import Trend
from social_posts.serializers import TrendSerializer


@api_view(['GET'])
def get_trends(request):
    serializer = TrendSerializer(Trend.objects.all(), many=True)

    return JsonResponse(serializer.data, safe=False)
