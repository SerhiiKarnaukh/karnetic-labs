from django.urls import path

from taberna_cart import views

urlpatterns = [
    path('', views.cart, name='cart'),
    path('add_cart/<int:product_id>/', views.add_cart, name='add_cart'),
    path('remove_cart/<int:product_id>/<int:cart_item_id>/',
         views.remove_cart,
         name='remove_cart'),
    path('remove_cart_item/<int:product_id>/<int:cart_item_id>/',
         views.remove_cart_item,
         name='remove_cart_item'),
    path('checkout/', views.checkout, name='checkout'),

    path('api/cart/', views.CartAPIView.as_view(), name='taberna_api_cart'),
    path('api/add-to-cart/<int:product_id>/', views.AddToCartView.as_view(), name='taberna_api_add_to_cart'),
    path('api/cart-remove/<int:product_id>/<int:cart_item_id>/',
         views.RemoveCartItemAPIView.as_view(), name='taberna_api_remove_cart'),
    path('api/cart-item-remove/<int:product_id>/<int:cart_item_id>/',
         views.RemoveCartItemFullyAPIView.as_view(), name='taberna_api_remove_cart_item_fully'),
]
