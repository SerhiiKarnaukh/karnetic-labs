import uuid

from taberna_cart.models import Cart, CartItem
from taberna_cart.utils.totals import calculate_cart_totals
from taberna_product.models import Variation
from taberna_profiles.models import UserProfile


def get_cart_id(request):
    cart_id = request.session.session_key
    if not cart_id:
        cart_id = request.session.create()
    return cart_id


def get_product_variations(product, post_data):
    """Getting product variations from POST data."""
    variations = []
    for key, value in post_data.items():
        if key == "cart_id":
            continue
        try:
            variation = Variation.objects.get(
                product=product,
                variation_category__iexact=key,
                variation_value__iexact=value
            )
            variations.append(variation)
        except Variation.DoesNotExist:
            continue
    return variations


def create_new_cart(cart_id=None):
    """Creates a new cart with a given or random ID."""
    new_cart_id = cart_id or str(uuid.uuid4())[:8].replace('-', '').lower()
    return Cart.objects.create(cart_id=new_cart_id)


def get_or_create_cart(request, cart_id=None):
    """
    Receiving or creating a shopping cart for an unauthenticated user.
    """
    if cart_id:
        cart = Cart.objects.filter(id=cart_id).first()
        return cart or create_new_cart()

    cart = Cart.objects.filter(cart_id=get_cart_id(request)).first()
    return cart or create_new_cart(get_cart_id(request))


def handle_cart_item(cart_items, product_variation, product, user=None, cart=None):
    """
    Processing adding an item to cart:
    - Increasing the quantity if a variation already exists.
    - Create a new entry if the variation is not found.
    """
    ex_var_list = []
    item_ids = []

    for item in cart_items:
        existing_variations = list(item.variations.all())
        ex_var_list.append(existing_variations)
        item_ids.append(item.id)

    if product_variation in ex_var_list:
        index = ex_var_list.index(product_variation)
        item_id = item_ids[index]
        item = CartItem.objects.get(id=item_id)
        item.quantity += 1
        item.save()
    else:
        item = CartItem.objects.create(
            product=product,
            quantity=1,
            user=user,
            cart=cart
        )
        if product_variation:
            item.variations.add(*product_variation)
        item.save()


def get_cart_for_request(request, user):
    """
    Helper function to retrieve the cart for the current user or guest.
    """
    if user.is_authenticated and UserProfile.objects.filter(user=user).exists():
        return None, UserProfile.objects.get(user=user)

    cart_id = None
    if hasattr(request, 'query_params'):
        cart_id = request.query_params.get('cart_id')

    if cart_id:
        cart = Cart.objects.filter(id=cart_id).first()
    else:
        cart = Cart.objects.get(cart_id=get_cart_id(request))

    return cart, None


def get_cart_item(request, product, cart_item_id):
    """
    Helper function to retrieve the cart item for the current user or guest.
    """
    cart, user_profile = get_cart_for_request(request, request.user)

    if user_profile:
        return CartItem.objects.get(product=product, user=user_profile, id=cart_item_id)
    return CartItem.objects.get(product=product, cart=cart, id=cart_item_id)


def get_cart_items(user, request):
    """
    Helper function to retrieve ALL cart items for the current user or guest.
    """
    cart, user_profile = get_cart_for_request(request, user)

    if user_profile:
        return CartItem.objects.filter(user=user_profile, is_active=True).order_by('-id')
    return CartItem.objects.filter(cart=cart, is_active=True).order_by('-id')


def prepare_cart_context(user, request):
    """
    Helper function to prepare the context for cart-related views.
    """
    try:
        cart_items = get_cart_items(user, request)
        total, quantity, tax, grand_total = calculate_cart_totals(cart_items)
    except Cart.DoesNotExist:
        cart_items = []
        total = quantity = tax = grand_total = 0

    return {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
