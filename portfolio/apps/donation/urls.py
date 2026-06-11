from django.urls import path

from donation import views

urlpatterns = [
    path('', views.my_donation, name='my-donation'),
    path('payment-success/', views.payment_success, name='payment-success'),
    path('payment-failed/', views.payment_failed, name='payment-failed'),
]
