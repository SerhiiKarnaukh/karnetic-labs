from django.db.models import Q

from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.models import Project
from core.serializers import ProjectSerializer

ANGULAR_CATEGORY_SLUG = 'angular'


class AngularAppsAPIList(generics.ListAPIView):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        return Project.objects.filter(category__slug=ANGULAR_CATEGORY_SLUG)


@api_view(['POST'])
def angular_search_api(request):
    query = request.data.get('query', '')

    if query:
        projects = Project.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            category__slug=ANGULAR_CATEGORY_SLUG,
        ).distinct()
        serialized_projects = ProjectSerializer(projects, many=True).data

        for project in serialized_projects:
            project['photo'] = request.build_absolute_uri(
                '/' + project['photo'].strip('/'))
            project['url'] = request.build_absolute_uri(
                '/' + project['url'].strip('/'))

        return Response(serialized_projects)

    return Response({'projects': []})
