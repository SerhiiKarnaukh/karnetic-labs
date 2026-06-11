from django.conf import settings
from django.db import transaction
from django.dispatch import receiver
from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received

from taberna_orders.models import Order
from taberna_orders.services.checkout import (
    clear_cart,
    create_order_products,
    create_payment,
    send_order_email,
    update_order,
)


@receiver(valid_ipn_received)
def paypal_taberna_payment_received(sender, **kwargs):
    ipn_obj = sender
    invoice = str(ipn_obj.invoice)
    txn_id = str(ipn_obj.txn_id)

    try:
        order = Order.objects.get(order_number=invoice)
    except Order.DoesNotExist:
        print(f"Order with invoice {invoice} does not exist.")
        return

    if ipn_obj.payment_status != ST_PP_COMPLETED:
        print(f"PayPal payment status not completed: {ipn_obj.payment_status}")
        return

    if ipn_obj.receiver_email != settings.PAYPAL_RECEIVER_EMAIL:
        print(f"Invalid receiver email: {ipn_obj.receiver_email}")
        return

    try:
        with transaction.atomic():
            payment = create_payment(order.user, txn_id, 'PayPal', order.order_total, ipn_obj.payment_status)
            update_order(order, payment)
            create_order_products(order, payment, order.user)
            clear_cart(order.user)
            send_order_email(order)
    except Exception as e:
        print(f"Error processing payment: {e}")
