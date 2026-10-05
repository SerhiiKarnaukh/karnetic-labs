from decimal import Decimal
from django.test import TestCase
from core.utils import create_active_user
from taberna_orders.models import Order, OrderProduct, Payment
from taberna_product.models import Category, Product
from taberna_profiles.models import UserProfile


class OrderModelsTest(TestCase):
    def test_model_helpers(self):
        user = create_active_user(
            email="order@example.com",
            username="order",
            password="pass123",
            first_name="Order",
            last_name="User",
        )
        profile = UserProfile.objects.create(user=user)
        category = Category.objects.create(name="Order", slug="order")
        product = Product.objects.create(category=category, created_by=profile, name="Item", slug="order-item", price=Decimal("4"), stock=2)
        payment = Payment.objects.create(user=profile, payment_id="pay", payment_method="Stripe", amount_paid="4", status="Completed")
        order = Order.objects.create(
            user=profile,
            payment=payment,
            order_number="1",
            first_name="Order",
            last_name="User",
            phone="1",
            email=user.email,
            address_line_1="Street",
            country="US",
            state="CA",
            city="LA",
            order_total=4,
            tax=0,
        )
        item = OrderProduct.objects.create(order=order, payment=payment, user=profile, product=product, quantity=1, product_price=4)
        self.assertEqual(order.full_name(), "Order User")
        self.assertEqual(order.full_address(), "Street ")
        self.assertEqual(str(order), "Order")
        self.assertEqual(str(payment), "pay")
        self.assertEqual(str(item), "Item")
