from rest_framework import serializers

from social_posts.models import Trend


class TrendSerializer(serializers.ModelSerializer):

    class Meta:
        model = Trend
        fields = (
            'id',
            'hashtag',
            'occurences',
        )
