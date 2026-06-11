import stripe
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from taberna_orders.models import Order
from taberna_orders.services.checkout import (
    clear_cart,
    create_order_products,
    create_payment,
    send_order_email,
    update_order,
)

stripe.api_key = settings.STRIPE_PRIVATE_KEY


def handle_stripe_webhook(request):
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    payload = request.body
    signature_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, signature_header, endpoint_secret
        )
    except stripe.error.StripeError:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        stripe_session_id = session.get('id')
        order = get_object_or_404(Order, stripe_checkout_session_id=stripe_session_id)

        if order.is_ordered:
            return HttpResponse(status=400)

        payment = create_payment(order.user, order.id, 'Stripe', order.order_total, 'Completed')
        update_order(order, payment)
        create_order_products(order, payment, order.user)
        clear_cart(order.user)
        send_order_email(order)

    return HttpResponse(status=200)
