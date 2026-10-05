from decimal import Decimal
from django.test import TestCase, override_settings
from taberna_cart.utils.totals import calculate_cart_totals


class CartTotalsTest(TestCase):
    @override_settings(TABERNA_TAX_RATE=Decimal("0.10"))
    def test_calculates_totals(self):
        product = type("Product", (), {"price": Decimal("12.50")})()
        item = type("Item", (), {"product": product, "quantity": 2})()
        self.assertEqual(calculate_cart_totals([item]), (Decimal("25.00"), 2, Decimal("2.50"), Decimal("27.50")))
