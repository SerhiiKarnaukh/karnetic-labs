from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from taberna_orders.models import Order
from taberna_orders.serializers import OrderSerializer


class UserOrdersListView(ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user.userprofile, is_ordered=True).order_by("-created_at")
