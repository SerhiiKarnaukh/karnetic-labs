from django.test import TestCase
from django.urls import reverse
from core.utils import create_active_user
from taberna_profiles.models import UserProfile

class DashboardViewsTest(TestCase):
    def test_dashboard_orders_and_profile_pages(self):
        user = create_active_user(email="dashboard@example.com", username="dashboard", password="pass123", first_name="Dash", last_name="Board")
        UserProfile.objects.create(user=user)
        self.client.force_login(user)
        for name in ("dashboard", "my_orders", "edit_profile", "change_password"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_edits_profile(self):
        user = create_active_user(email="edit@example.com", username="edit", password="pass123", first_name="Edit", last_name="User")
        UserProfile.objects.create(user=user)
        self.client.force_login(user)
        response = self.client.post(reverse("edit_profile"), {"first_name":"Updated","last_name":"User","phone_number":"2","address_line_1":"Street","address_line_2":"","city":"City","state":"State","country":"US"})
        self.assertEqual(response.status_code, 302)

    def test_order_detail_page(self):
        from decimal import Decimal
        from taberna_orders.models import Order, OrderProduct
        from taberna_product.models import Category, Product
        user = create_active_user(email="detail@example.com", username="detail", password="pass123", first_name="Detail", last_name="User")
        profile = UserProfile.objects.create(user=user)
        category = Category.objects.create(name="Detail", slug="detail")
        product = Product.objects.create(category=category, created_by=profile, name="Item", slug="detail-item", price=Decimal("2"), stock=1)
        order = Order.objects.create(user=profile, order_number="123", first_name="A", last_name="B", phone="1", email=user.email, address_line_1="Street", country="US", state="CA", city="LA", order_total=2, tax=0)
        OrderProduct.objects.create(order=order, user=profile, product=product, quantity=1, product_price=2)
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("order_detail", args=[123])).status_code, 200)
