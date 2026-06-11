from rest_framework import serializers

from taberna_product.models import Category
from taberna_product.serializers.products import ProductSerializer


class CategorySerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "get_absolute_url",
            "products",
        )

    def get_products(self, obj):
        filtered_products = obj.products.filter(stripe_product_id__isnull=False).exclude(stripe_product_id="")
        return ProductSerializer(filtered_products, many=True, context=self.context).data


class AllCategoriesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "get_absolute_url",
        )
