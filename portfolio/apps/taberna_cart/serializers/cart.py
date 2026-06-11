from rest_framework import serializers

from taberna_cart.models import CartItem
from taberna_product.serializers import ProductSerializer, VariationSerializer


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    variations = VariationSerializer(many=True)
    sub_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ('id', 'product', 'variations', 'quantity', 'is_active', 'sub_total')

    def get_sub_total(self, obj):
        return obj.sub_total()
