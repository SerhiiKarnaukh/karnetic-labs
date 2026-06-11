from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http import JsonResponse

from rest_framework.decorators import api_view

from social_notification.utils import create_notification
from social_profiles.models import Profile
from social_chat.models import Conversation, ConversationMessage
from social_chat.serializers import ConversationMessageSerializer


@api_view(['POST'])
def conversation_send_message(request, pk):
    request_user = Profile.objects.get(user=request.user)
    conversation = Conversation.objects.filter(
        users__in=list([request_user])).get(pk=pk)

    for user in conversation.users.all():
        if user != request_user:
            sent_to = user

    conversation_message = ConversationMessage.objects.create(
        conversation=conversation,
        body=request.data.get('body'),
        created_by=request_user,
        sent_to=sent_to,
    )

    serializer = ConversationMessageSerializer(
        conversation_message,
        context={'request': request},
    )

    create_notification(request, 'chat_message', conversation_message_id=conversation_message.id)

    channel_layer = get_channel_layer()
    group_name = f'social_chat_{conversation.id}'
    async_to_sync(channel_layer.group_send)(group_name, {
        'type': 'send_message',
        'message': serializer.data
    })

    return JsonResponse(serializer.data, safe=False)
