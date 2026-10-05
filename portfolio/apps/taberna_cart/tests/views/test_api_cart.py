from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from core.utils import create_active_user
from taberna_cart.models import CartItem
from taberna_product.models import Category, Product
from taberna_profiles.models import UserProfile

class CartApiViewsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        user = create_active_user(email="api-cart@example.com", username="api-cart", password="pass123", first_name="Api", last_name="Cart")
        profile = UserProfile.objects.create(user=user)
        category = Category.objects.create(name="Api", slug="api-cart")
        self.product = Product.objects.create(category=category, created_by=profile, name="Item", slug="api-item", price=Decimal("5"), stock=2)

    def test_guest_add_get_and_delete(self):
        response = self.client.post(reverse("taberna_api_add_to_cart", args=[self.product.id]), {}, format="json")
        cart_id, item = response.data["cart_id"], CartItem.objects.get()
        self.assertEqual(self.client.get(reverse("taberna_api_cart") + f"?cart_id={cart_id}").data["quantity"], 1)
        url = reverse("taberna_api_remove_cart", args=[self.product.id, item.id]) + f"?cart_id={cart_id}"
        self.assertEqual(self.client.delete(url).status_code, 200)
        self.assertEqual(self.client.delete(url).status_code, 404)

    def test_fully_removes_item(self):
        response = self.client.post(reverse("taberna_api_add_to_cart", args=[self.product.id]), {}, format="json")
        item = CartItem.objects.get()
        url = reverse("taberna_api_remove_cart_item_fully", args=[self.product.id, item.id]) + f"?cart_id={response.data['cart_id']}"
        self.assertEqual(self.client.delete(url).status_code, 200)

    def test_authenticated_add_and_missing_remove(self):
        from taberna_profiles.models import UserProfile
        user = UserProfile.objects.get(user__email="api-cart@example.com").user
        self.client.force_authenticate(user)
        self.assertEqual(self.client.post(reverse("taberna_api_add_to_cart", args=[self.product.id]), {}, format="json").status_code, 200)
        self.assertEqual(self.client.delete(reverse("taberna_api_remove_cart", args=[self.product.id, 99])).status_code, 404)
        self.assertEqual(self.client.delete(reverse("taberna_api_remove_cart_item_fully", args=[self.product.id, 99])).status_code, 404)

    def test_api_remove_decrements_quantity(self):
        response = self.client.post(reverse("taberna_api_add_to_cart", args=[self.product.id]), {}, format="json")
        item = CartItem.objects.get()
        item.quantity = 2
        item.save()
        url = reverse("taberna_api_remove_cart", args=[self.product.id, item.id]) + f"?cart_id={response.data['cart_id']}"
        self.assertEqual(self.client.delete(url).status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 1)
