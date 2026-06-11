from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from taberna_cart.models import Cart, CartItem
from taberna_cart.serializers import CartItemSerializer
from taberna_cart.utils import (
    get_cart_item,
    get_or_create_cart,
    get_product_variations,
    handle_cart_item,
    prepare_cart_context,
)
from taberna_product.models import Product
from taberna_profiles.models import UserProfile


class CartAPIView(APIView):

    def get(self, request, *args, **kwargs):
        context = prepare_cart_context(request.user, request)
        serialized_data = {
            'total': context['total'],
            'quantity': context['quantity'],
            'tax': context['tax'],
            'grand_total': context['grand_total'],
            'cart_items': CartItemSerializer(
                context['cart_items'],
                many=True,
                context={"request": request}
            ).data,
        }
        return Response(serialized_data)


class AddToCartView(APIView):
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        product_variation = get_product_variations(product, request.data)
        cart_id = request.data.get('cart_id')

        if request.user.is_authenticated and UserProfile.objects.filter(user=request.user).exists():
            current_user = UserProfile.objects.get(user=request.user)
            cart_items = CartItem.objects.filter(user=current_user, product=product)
            handle_cart_item(cart_items, product_variation, product, user=current_user)
        else:
            cart = get_or_create_cart(request, cart_id=cart_id)
            cart_id = cart.id
            cart_items = CartItem.objects.filter(cart=cart, product=product)
            handle_cart_item(cart_items, product_variation, product, cart=cart)

        return Response({"message": "Product added to cart successfully", "cart_id": cart_id}, status=status.HTTP_200_OK)


class RemoveCartItemAPIView(APIView):

    def delete(self, request, product_id, cart_item_id):

        product = get_object_or_404(Product, id=product_id)

        try:
            cart_item = get_cart_item(request, product, cart_item_id)

            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()

            return Response({"message": "Item removed from cart"}, status=status.HTTP_200_OK)

        except (Cart.DoesNotExist, CartItem.DoesNotExist):
            return Response({"error": "Cart item does not exist"}, status=status.HTTP_404_NOT_FOUND)


class RemoveCartItemFullyAPIView(APIView):
    def delete(self, request, product_id, cart_item_id):
        product = get_object_or_404(Product, id=product_id)

        try:
            cart_item = get_cart_item(request, product, cart_item_id)
            cart_item.delete()

            return Response({"message": "Cart item deleted successfully"}, status=status.HTTP_200_OK)

        except (Cart.DoesNotExist, CartItem.DoesNotExist):
            return Response({"error": "Cart item does not exist"}, status=status.HTTP_404_NOT_FOUND)
