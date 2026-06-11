from django.urls import path

from taberna_orders import views

urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path('order_complete/<int:order_number>/', views.order_complete, name='order_complete'),
    path('order_failed/', views.order_failed, name='order_failed'),
    path('stripe_webhook/', views.stripe_webhook, name='stripe_webhook'),

    path('api/v1/place_order_stripe_charge/',
         views.PlaceOrderStripeChargeAPIView.as_view(), name='taberna_api_place_order_charge'),
    path('api/v1/place_order_stripe_session/',
         views.PlaceOrderStripeSessionAPIView.as_view(), name='taberna_api_place_order_session'),
    path('api/v1/order_payment_success/',
         views.OrderPaymentSuccessAPIView.as_view(), name='taberna_api_payment_success'),
    path('api/v1/order_payment_failed/',
         views.OrderPaymentFailedAPIView.as_view(), name='taberna_api_payment_failed'),
]
