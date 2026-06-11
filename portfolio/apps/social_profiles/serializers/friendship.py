from rest_framework import serializers

from social_profiles.models import FriendshipRequest
from social_profiles.serializers.profile import ProfileSerializer


class FriendshipRequestSerializer(serializers.ModelSerializer):
    created_by = ProfileSerializer(read_only=True)

    class Meta:
        model = FriendshipRequest
        fields = (
            'id',
            'created_by',
        )
