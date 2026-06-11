from rest_framework import serializers

from social_posts.models import Post
from social_posts.serializers.comment import CommentSerializer
from social_posts.serializers.post import PostAttachmentSerializer
from social_profiles.serializers import ProfileSerializer


class PostDetailSerializer(serializers.ModelSerializer):
    created_by = ProfileSerializer(read_only=True)
    comments = CommentSerializer(read_only=True, many=True)
    attachments = PostAttachmentSerializer(read_only=True, many=True)

    class Meta:
        model = Post
        fields = (
            'id',
            'body',
            'likes_count',
            'comments_count',
            'created_by',
            'created_at_formatted',
            'comments',
            'attachments',
        )
