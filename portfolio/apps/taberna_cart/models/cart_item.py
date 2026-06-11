from django.db import models

from taberna_cart.models.cart import Cart
from taberna_product.models import Product, Variation
from taberna_profiles.models import UserProfile


class CartItem(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variations = models.ManyToManyField(Variation, blank=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField()
    is_active = models.BooleanField(default=True)

    def sub_total(self):
        return self.product.price * self.quantity

    def __unicode__(self):
        return self.product
