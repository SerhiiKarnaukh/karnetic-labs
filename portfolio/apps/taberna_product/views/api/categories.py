from django.db.models import Count
from django.http import Http404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from taberna_product.models import Category
from taberna_product.serializers import AllCategoriesSerializer, CategorySerializer


class CategoryAPIDetail(generics.RetrieveAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Http404:
            return Response({'error': 'Category not found.'},
                            status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())

        slug = self.kwargs.get('category_slug', None)
        if slug is not None:
            queryset = queryset.filter(slug=slug)

        try:
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404("No matching query result was found.")

        self.check_object_permissions(self.request, obj)

        return obj


class ProductCategoryAPIView(APIView):

    def get(self, request):
        categories = Category.objects.annotate(one=Count('products')).filter(
            one__gt=0)
        serializer = AllCategoriesSerializer(categories, many=True)
        return Response(serializer.data)
