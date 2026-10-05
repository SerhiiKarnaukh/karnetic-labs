from decimal import Decimal
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from core.utils import create_active_user
from taberna_cart.models import Cart, CartItem
from taberna_cart.utils.cart import create_new_cart, get_cart_for_request, get_cart_id, get_cart_item, get_cart_items, get_or_create_cart, get_product_variations, handle_cart_item, prepare_cart_context
from taberna_product.models import Category, Product, Variation
from taberna_profiles.models import UserProfile

class CartUtilsTest(TestCase):
    def setUp(self):
        self.user = create_active_user(email="cart@example.com", username="cart", password="pass123", first_name="Cart", last_name="User")
        self.profile = UserProfile.objects.create(user=self.user)
        category = Category.objects.create(name="Coffee", slug="coffee")
        self.product = Product.objects.create(category=category, created_by=self.profile, name="Beans", slug="beans", price=Decimal("10.00"), stock=5)
        self.variation = Variation.objects.create(product=self.product, variation_category="color", variation_value="Red")

    def make_request(self, user=None):
        request = RequestFactory().get("/")
        SessionMiddleware(lambda request: None).process_request(request)
        request.session.save()
        request.user = user or type("Guest", (), {"is_authenticated": False})()
        return request

    def test_guest_cart_helpers(self):
        request = self.make_request()
        cart = get_or_create_cart(request)
        self.assertEqual(cart.cart_id, get_cart_id(request))
        self.assertEqual(get_or_create_cart(request), cart)
        self.assertEqual(get_or_create_cart(request, cart.id), cart)
        self.assertIsNotNone(create_new_cart())
        self.assertEqual(get_product_variations(self.product, {"color": "red", "bad": "x", "cart_id": "1"}), [self.variation])

    def test_items_and_context_for_user(self):
        handle_cart_item([], [self.variation], self.product, user=self.profile)
        item = CartItem.objects.get()
        handle_cart_item([item], [self.variation], self.product, user=self.profile)
        item.refresh_from_db()
        request = self.make_request(self.user)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(get_cart_for_request(request, self.user)[1], self.profile)
        self.assertEqual(get_cart_item(request, self.product, item.id), item)
        self.assertEqual(list(get_cart_items(self.user, request)), [item])
        self.assertEqual(prepare_cart_context(self.user, request)["grand_total"], Decimal("20.40"))

    def test_missing_guest_cart_has_empty_context(self):
        self.assertEqual(prepare_cart_context(self.make_request().user, self.make_request())["quantity"], 0)
