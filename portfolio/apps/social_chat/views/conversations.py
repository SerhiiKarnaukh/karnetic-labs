from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound

from social_profiles.models import Profile
from social_chat.models import Conversation
from social_chat.serializers import ConversationDetailSerializer, ConversationSerializer


@api_view(['GET'])
def conversation_list(request):
    request_user = Profile.objects.get(user=request.user)
    conversations = Conversation.objects.filter(users__in=list([request_user]))
    serializer = ConversationSerializer(
        conversations,
        context={'request': request},
        many=True,
    )

    return JsonResponse(serializer.data, safe=False)


@api_view(['GET'])
def conversation_detail(request, pk):
    request_user = Profile.objects.get(user=request.user)
    try:
        conversation = Conversation.objects.filter(
            users__in=[request_user]
        ).get(pk=pk)
    except Conversation.DoesNotExist:
        raise NotFound("Conversation not found.")

    serializer = ConversationDetailSerializer(
        conversation,
        context={'request': request},
    )

    return JsonResponse(serializer.data, safe=False)


@api_view(['GET'])
def conversation_get_or_create(request, slug):
    user = get_object_or_404(Profile, slug=slug)
    request_user = Profile.objects.get(user=request.user)

    conversations = Conversation.objects.filter(
        users__in=list([request_user])).filter(users__in=list([user]))

    if conversations.exists():
        conversation = conversations.first()
    else:
        conversation = Conversation.objects.create()
        conversation.users.add(user, request_user)
        conversation.save()

    serializer = ConversationDetailSerializer(
        conversation,
        context={'request': request},
    )

    return JsonResponse(serializer.data, safe=False)
