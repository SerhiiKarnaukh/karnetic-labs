from rest_framework import generics

from core.serializers import TopbarLinkSerializer
from core.utils.topbar_links import get_active_topbar_links


class TopbarLinksAPIList(generics.ListAPIView):
    serializer_class = TopbarLinkSerializer

    def get_queryset(self):
        return get_active_topbar_links()
