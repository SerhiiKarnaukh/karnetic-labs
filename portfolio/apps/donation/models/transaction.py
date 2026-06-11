from django.db import models


class Transaction(models.Model):
    invoice = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=4, decimal_places=2)
    paid = models.BooleanField(default=False)
