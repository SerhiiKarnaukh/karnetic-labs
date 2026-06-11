import datetime

import stripe
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from taberna_cart.models import CartItem
from taberna_orders.models import Order, OrderProduct, Payment

stripe.api_key = settings.STRIPE_PRIVATE_KEY


def create_order_from_form(form, user_profile, grand_total, tax, request):
    """
    Creates an Order object based on a form and additional data.
    """
    order = Order(
        user=user_profile,
        first_name=form.cleaned_data['first_name'],
        last_name=form.cleaned_data['last_name'],
        phone=form.cleaned_data['phone'],
        email=form.cleaned_data['email'],
        address_line_1=form.cleaned_data['address_line_1'],
        address_line_2=form.cleaned_data['address_line_2'],
        country=form.cleaned_data['country'],
        state=form.cleaned_data['state'],
        city=form.cleaned_data['city'],
        order_note=form.cleaned_data['order_note'],
        order_total=grand_total,
        tax=tax,
        ip=request.META.get('REMOTE_ADDR'),
    )
    order.save()
    return order


def generate_order_number(order):
    """
    Generates a unique order number.
    """
    current_date = datetime.date.today().strftime("%Y%m%d")
    return f"{current_date}{order.id}"


def create_payment(user, txn_id, payment_method, amount_paid, status):
    payment = Payment(
        user=user,
        payment_id=txn_id,
        payment_method=payment_method,
        amount_paid=amount_paid,
        status=status,
    )
    payment.save()
    return payment


def update_order(order, payment):
    order.payment = payment
    order.is_ordered = True
    order.save()


def create_order_products(order, payment, user):
    cart_items = CartItem.objects.filter(user=user)
    for item in cart_items:
        order_product = OrderProduct.objects.create(
            order=order,
            payment=payment,
            user=user,
            product=item.product,
            quantity=item.quantity,
            product_price=item.product.price,
            ordered=True,
        )
        order_product.variations.set(item.variations.all())
        order_product.save()

        product = item.product
        product.stock -= item.quantity
        product.save()


def clear_cart(user):
    CartItem.objects.filter(user=user).delete()


def send_order_email(order):
    user = order.user
    mail_subject = 'Thank you for your order!'
    message = render_to_string('taberna_orders/order_received_email.html', {
        'user': user.user,
        'order': order,
    })
    to_email = user.user.email
    email = EmailMessage(mail_subject, message, to=[to_email])
    email.send()


def stripe_charge_create(request, amount, order):
    stripe_token = request.data.get('stripe_token')
    stripe.Charge.create(
        amount=int(amount * 100),
        currency='USD',
        description=f'Order #{order.order_number}',
        source=stripe_token,
        receipt_email=request.user.email
    )


def get_tax_rate():
    try:
        tax_rates = stripe.TaxRate.list(active=True).data
        for tax_rate in tax_rates:
            if tax_rate.display_name == "VAT":
                return tax_rate
    except stripe.error.StripeError as e:
        print(f"Error when receiving tax: {e}")
    return None


def stripe_session_create(cart_items, customer_email, base_url):
    line_items = []
    tax_rate = get_tax_rate()
    for item in cart_items:
        prices = stripe.Price.list(product=item.product.stripe_product_id)
        price = prices.data[0]
        line_items.append({
            'price': price.id,
            'quantity': item.quantity,
            'tax_rates': [tax_rate.id] if tax_rate else []
        })

    checkout_session = stripe.checkout.Session.create(
        line_items=line_items,
        payment_method_types=['card'],
        mode='payment',
        customer_creation='always',
        success_url=f'{base_url}/taberna/cart/success?session_id={{CHECKOUT_SESSION_ID}}',
        cancel_url=f'{base_url}/taberna/cart/failed?session_id={{CHECKOUT_SESSION_ID}}',
        customer_email=customer_email,
    )
    return checkout_session
