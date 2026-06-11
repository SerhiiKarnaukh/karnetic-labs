from rest_framework import serializers

from taberna_product.models import Product, ProductGallery, ReviewRating, Variation


class ProductGallerySerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductGallery
        fields = (
            "id",
            "image",
        )


class ProductSerializer(serializers.ModelSerializer):

    productgallery = ProductGallerySerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "image",
            "get_absolute_url",
            "description",
            "price",
            "productgallery",
        )

    def create(self, validated_data):
        images_data = self.context.get('view').request.FILES
        product = Product.objects.create(**validated_data)
        for image_data in images_data.values():
            ProductGallery.objects.create(product=product, image=image_data)
        return product


class ReviewRatingSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = ReviewRating
        fields = [
            "id",
            "user",
            "subject",
            "review",
            "rating",
            "created_at",
            "updated_at",
        ]

    def get_user(self, obj):
        return f'{obj.user.user.first_name} {obj.user.user.last_name}'


class VariationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variation
        fields = ('id', 'variation_category', 'variation_value')
