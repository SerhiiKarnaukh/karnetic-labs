from django.db.models import Q
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response

from taberna_product.models import Product, ReviewRating, Variation
from taberna_product.serializers import ProductSerializer, ReviewRatingSerializer


class LatestProductsAPIList(generics.ListAPIView):
    queryset = Product.objects.filter(is_available=True).exclude(
        stripe_product_id__isnull=True).exclude(stripe_product_id="")[:6]
    serializer_class = ProductSerializer


class ProductAPIDetail(generics.RetrieveAPIView):
    lookup_url_kwarg = 'product_slug'
    lookup_field = 'slug'
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get(self, request, *args, **kwargs):
        product = self.get_object()
        related_products = Product.objects.filter(
            category=product.category
        ).exclude(id=product.id).exclude(
            stripe_product_id__isnull=True).exclude(stripe_product_id="")
        reviews = ReviewRating.objects.filter(product=product, status=True)

        variations = {
            "colors": Variation.objects.colors().filter(product=product).values('id', 'variation_value'),
            "sizes": Variation.objects.sizes().filter(product=product).values('id', 'variation_value'),
        }

        data = {
            "product": self.get_serializer(product).data,
            "related_products": ProductSerializer(
                related_products, many=True, context={"request": request}
            ).data,
            "reviews": ReviewRatingSerializer(reviews, many=True).data,
            "variations": variations,
        }
        return Response(data)


@api_view(['POST'])
def search_api(request):
    query = request.data.get('query', '')

    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).filter(
            is_available=True
        ).exclude(
            stripe_product_id__isnull=True
        ).exclude(
            stripe_product_id=""
        )
        serialized_products = []
        for product in products:
            product_data = ProductSerializer(product).data
            product_data['image'] = request.build_absolute_uri(
                product.image.url)
            serialized_products.append(product_data)
        return Response(serialized_products)
    else:
        return Response({"products": []})
