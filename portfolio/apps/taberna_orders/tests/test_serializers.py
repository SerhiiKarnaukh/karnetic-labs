from decimal import Decimal
from django.test import TestCase
from core.utils import create_active_user
from taberna_orders.models import Order, Payment
from taberna_orders.serializers import OrderSerializer
from taberna_profiles.models import UserProfile


class OrderSerializerTest(TestCase):
    def test_serializes_order(self):
        user = create_active_user(
            email="order-serial@example.com",
            username="order-serial",
            password="pass123",
            first_name="Order",
            last_name="Serial",
        )
        profile = UserProfile.objects.create(user=user)
        payment = Payment.objects.create(user=profile, payment_id="pay", payment_method="Stripe", amount_paid="1", status="Done")
        order = Order.objects.create(
            user=profile,
            payment=payment,
            order_number="1",
            first_name="A",
            last_name="B",
            phone="1",
            email=user.email,
            address_line_1="X",
            country="US",
            state="CA",
            city="LA",
            order_total=Decimal("1"),
            tax=0,
        )
        self.assertEqual(OrderSerializer(order).data["payment"]["payment_id"], "pay")
