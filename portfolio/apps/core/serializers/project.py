from rest_framework import serializers

from core.models import Project


class ProjectSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = (
            "id",
            "title",
            "photo",
            "github_url",
            "view_url",
            'url',
        )

    def get_url(self, obj):
        url = obj.get_absolute_url()
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(url)
        return url
