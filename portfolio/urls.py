from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

urlpatterns = [
    path("ckeditor5/", include('django_ckeditor_5.urls'), name="ck_editor_5_upload_file"),
    path('admin/', admin.site.urls),

    # Djoser
    path('api/v1/auth', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.authtoken')),
    # JWT
    path('api/v1/token/',
         TokenObtainPairView.as_view(),
         name='token_obtain_pair'),
    path('api/v1/token/refresh/',
         TokenRefreshView.as_view(),
         name='token_refresh'),
    path('api/v1/token/verify/',
         TokenVerifyView.as_view(),
         name='token_verify'),

    # for Applications Manager
    path('', include('core.urls')),

    # for Taberna
    path('taberna-cart/', include('taberna_cart.urls')),
    path('taberna-store/', include('taberna_product.urls')),
    path('taberna-profiles/', include('taberna_profiles.urls')),
    path('taberna-orders/', include('taberna_orders.urls')),

    # for Social Network
    path('api/social-posts/', include('social_posts.urls')),
    path('api/social-profiles/', include('social_profiles.urls')),
    path('api/social-chat/', include('social_chat.urls')),
    path('api/social-notifications/', include('social_notification.urls')),

    # for Donation
    path('paypal/', include("paypal.standard.ipn.urls")),
    path('donation/', include('donation.urls')),

    # for AI Lab
    path('ai-lab/', include('ai_lab.urls')),

    # for F1 Pit Wall Command Center
    path('f1/', include('f1_pitwall.urls')),

]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
