from rest_framework import serializers

from taberna_orders.models import Order, OrderProduct, Payment
from taberna_product.serializers import ProductSerializer, VariationSerializer


class PaymentSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%b. %d, %Y, %I:%M %p")

    class Meta:
        model = Payment
        fields = [
            "payment_id",
            "payment_method",
            "amount_paid",
            "status",
            "created_at",
        ]


class OrderProductSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    variations = VariationSerializer(many=True)

    class Meta:
        model = OrderProduct
        fields = [
            "id",
            "product",
            "variations",
            "quantity",
            "product_price",
            "ordered",
        ]


class OrderSerializer(serializers.ModelSerializer):
    order_products = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(format="%b. %d, %Y, %I:%M %p")
    payment = PaymentSerializer()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "first_name",
            "last_name",
            "phone",
            "email",
            "address_line_1",
            "address_line_2",
            "country",
            "state",
            "city",
            "order_note",
            "order_total",
            "tax",
            "status",
            "ip",
            "is_ordered",
            "created_at",
            "payment",
            "updated_at",
            "order_products",
        ]

    def get_order_products(self, obj):
        return OrderProductSerializer(
            obj.orderproduct_set.all(), many=True, context=self.context
        ).data
