from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from taberna_cart.models import CartItem
from taberna_cart.utils import calculate_cart_totals
from taberna_orders.forms import OrderForm
from taberna_orders.models import Order
from taberna_orders.services.checkout import (
    clear_cart,
    create_order_from_form,
    create_order_products,
    create_payment,
    generate_order_number,
    send_order_email,
    stripe_charge_create,
    stripe_session_create,
    update_order,
)


class PlaceOrderStripeChargeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user_profile = request.user.userprofile
        cart_items = CartItem.objects.filter(user=user_profile)

        if not cart_items.exists():
            return Response({"error": "Your cart is empty!"}, status=status.HTTP_400_BAD_REQUEST)

        total, quantity, tax, grand_total = calculate_cart_totals(cart_items)

        form = OrderForm(request.data)
        if form.is_valid():
            order = create_order_from_form(form, user_profile, grand_total, tax, request)
            order.order_number = generate_order_number(order)
            order.save()

            try:
                with transaction.atomic():
                    stripe_charge_create(request, grand_total, order)
                    payment = create_payment(order.user, order.id, 'Stripe', order.order_total, 'Completed')
                    update_order(order, payment)
                    create_order_products(order, payment, order.user)
                    clear_cart(order.user)
                    send_order_email(order)
            except Exception as e:
                return Response(
                    {"errors": {"message": str(e), "type": e.__class__.__name__}},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response({
                "order": {
                    "id": order.id,
                    "order_number": order.order_number,
                    "grand_total": grand_total,
                    "tax": tax,
                    "status": order.status,
                    'total': total,
                    'quantity': quantity,
                },
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({"errors": form.errors}, status=status.HTTP_400_BAD_REQUEST)


class PlaceOrderStripeSessionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user_profile = request.user.userprofile
        cart_items = CartItem.objects.filter(user=user_profile)

        if not cart_items.exists():
            return Response({"error": "Your cart is empty!"}, status=status.HTTP_400_BAD_REQUEST)

        _, _, tax, grand_total = calculate_cart_totals(cart_items)

        form = OrderForm(request.data)
        if form.is_valid():
            base_url = request.META['HTTP_ORIGIN']
            customer_email = form.cleaned_data['email']
            try:
                with transaction.atomic():
                    checkout_session = stripe_session_create(cart_items, customer_email, base_url)
                    order = create_order_from_form(form, user_profile, grand_total, tax, request)
                    order.order_number = generate_order_number(order)
                    order.stripe_checkout_session_id = checkout_session.id
                    order.save()
            except Exception as e:
                return Response(
                    {"errors": {"message": str(e), "type": e.__class__.__name__}},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response({"checkout_url": checkout_session.url}, status=status.HTTP_200_OK)
        else:
            return Response({"errors": form.errors}, status=status.HTTP_400_BAD_REQUEST)


class OrderPaymentSuccessAPIView(APIView):

    def post(self, request, *args, **kwargs):
        if not settings.DEBUG:
            return Response({"error": "This endpoint is available only in DEBUG mode"}, status=status.HTTP_403_FORBIDDEN)

        stripe_session_id = request.data.get("stripe_session_id")
        order = get_object_or_404(Order, stripe_checkout_session_id=stripe_session_id)

        if order.is_ordered:
            return Response({"message": "Order already processed"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                payment = create_payment(order.user, order.id, 'Stripe', order.order_total, 'Completed')
                update_order(order, payment)
                create_order_products(order, payment, order.user)
                clear_cart(order.user)
                send_order_email(order)

            return Response({"message": "Order successfully completed"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class OrderPaymentFailedAPIView(APIView):
    def post(self, request, *args, **kwargs):
        stripe_session_id = request.data.get("stripe_session_id")
        order = get_object_or_404(Order, stripe_checkout_session_id=stripe_session_id)

        try:
            order.delete()
            return Response({"message": "Order deleted due to failed payment"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
