from datetime import timedelta
from django.test import TestCase
from django.utils.timezone import now
from taberna_cart.models import Cart
from taberna_cart.tasks.cart import delete_old_carts


class CartTasksTest(TestCase):
    def test_deletes_only_old_carts(self):
        old = Cart.objects.create(cart_id="old")
        Cart.objects.filter(pk=old.pk).update(date_added=(now() - timedelta(days=61)).date())
        current = Cart.objects.create(cart_id="current")
        delete_old_carts.apply().get()
        self.assertFalse(Cart.objects.filter(pk=old.pk).exists())
        self.assertTrue(Cart.objects.filter(pk=current.pk).exists())
