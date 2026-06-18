from rest_framework import serializers

from core.models import TopbarLink


class TopbarLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = TopbarLink
        fields = ('key', 'url', 'title', 'icon_class', 'ordering')
