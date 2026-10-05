from decimal import Decimal
from django.test import TestCase
from core.utils import create_active_user
from taberna_cart.models import Cart, CartItem
from taberna_product.models import Category, Product
from taberna_profiles.models import UserProfile

class CartModelsTest(TestCase):
    def test_cart_and_item_values(self):
        user = create_active_user(email="model@example.com", username="model", password="pass123", first_name="Model", last_name="User")
        profile = UserProfile.objects.create(user=user)
        category = Category.objects.create(name="Tea", slug="tea")
        product = Product.objects.create(category=category, created_by=profile, name="Tea", slug="tea-product", price=Decimal("4.50"), stock=1)
        cart = Cart.objects.create(cart_id="cart")
        item = CartItem.objects.create(cart=cart, product=product, quantity=3)
        self.assertEqual(str(cart), "cart")
        self.assertEqual(item.sub_total(), Decimal("13.50"))
        self.assertEqual(item.__unicode__(), product)
