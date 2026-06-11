from celery import shared_task
from datetime import timedelta

from django.utils.timezone import now

from taberna_cart.models import Cart


@shared_task(name='taberna_cart.tasks.delete_old_carts')
def delete_old_carts():
    threshold_date = now() - timedelta(days=60)
    old_carts = Cart.objects.filter(date_added__lt=threshold_date)
    old_carts.delete()
