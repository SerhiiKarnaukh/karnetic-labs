from rest_framework import serializers

from social_profiles.serializers import ProfileSerializer
from social_chat.models import Conversation, ConversationMessage


class ConversationSerializer(serializers.ModelSerializer):
    users = ProfileSerializer(read_only=True, many=True)

    class Meta:
        model = Conversation
        fields = (
            'id',
            'users',
            'modified_at_formatted',
        )


class ConversationMessageSerializer(serializers.ModelSerializer):
    sent_to = ProfileSerializer(read_only=True)
    created_by = ProfileSerializer(read_only=True)

    class Meta:
        model = ConversationMessage
        fields = (
            'id',
            'sent_to',
            'created_by',
            'created_at_formatted',
            'body',
        )


class ConversationDetailSerializer(serializers.ModelSerializer):
    messages = ConversationMessageSerializer(read_only=True, many=True)

    class Meta:
        model = Conversation
        fields = (
            'id',
            'users',
            'modified_at_formatted',
            'messages',
        )
