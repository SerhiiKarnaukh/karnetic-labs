from taberna_cart.models import Cart, CartItem
from taberna_cart.utils import get_cart_id
from taberna_profiles.models import UserProfile


def counter(request):
    cart_count = 0
    if 'admin' in request.path:
        return {}
    else:
        try:
            cart = Cart.objects.filter(cart_id=get_cart_id(request))
            if request.user.is_authenticated and UserProfile.objects.filter(user=request.user).exists():
                request_user = UserProfile.objects.get(user=request.user)
                cart_items = CartItem.objects.all().filter(user=request_user)
            else:
                cart_items = CartItem.objects.all().filter(cart=cart[:1])
            for cart_item in cart_items:
                cart_count += cart_item.quantity
        except Cart.DoesNotExist:
            cart_count = 0
    return dict(cart_count=cart_count)
