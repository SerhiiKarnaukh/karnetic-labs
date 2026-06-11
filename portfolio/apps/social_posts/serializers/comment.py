from rest_framework import serializers

from social_posts.models import Comment
from social_profiles.serializers import ProfileSerializer


class CommentSerializer(serializers.ModelSerializer):
    created_by = ProfileSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = (
            'id',
            'body',
            'created_by',
            'created_at_formatted',
        )
