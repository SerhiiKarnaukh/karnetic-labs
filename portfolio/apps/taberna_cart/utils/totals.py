from django.conf import settings
from decimal import Decimal


def calculate_cart_totals(cart_items):
    total = sum(item.product.price * item.quantity for item in cart_items)
    quantity = sum(item.quantity for item in cart_items)
    tax_rate = Decimal(getattr(settings, 'TABERNA_TAX_RATE', 0.02))
    tax = round(total * tax_rate, 2)
    grand_total = total + tax
    return total, quantity, tax, grand_total
