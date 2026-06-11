from django.urls import path

from taberna_profiles import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('activate-result/', views.activate_result, name='activate_result'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.dashboard, name='dashboard'),
    path('forgot_password/', views.forgotPassword, name='forgotPassword'),
    path('reset_password_validate/<uidb64>/<token>/',
         views.resetpassword_validate,
         name='resetpassword_validate'),
    path('reset_password/', views.resetPassword, name='resetPassword'),
    path('change_password/', views.change_password, name='change_password'),
    path('my_orders/', views.my_orders, name='my_orders'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('change_password/', views.change_password, name='change_password'),
    path('order_detail/<int:order_id>/',
         views.order_detail,
         name='order_detail'),

    path('api/register/', views.TabernaProfileCreateView.as_view(), name='taberna-api-register'),
    path('api/v1/orders/', views.UserOrdersListView.as_view(), name="taberna-api-user-orders"),
    path('api/v1/token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
]
