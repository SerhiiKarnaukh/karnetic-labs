from django.urls import path

from taberna_product import views

urlpatterns = [
    path('', views.FrontPage.as_view(), name='frontpage'),
    path('shop/', views.CategoryDetail.as_view(), name='store'),
    path('category/<slug:slug>/',
         views.CategoryDetail.as_view(),
         name='category_detail'),
    path('category/<slug:category_slug>/<slug:slug>/',
         views.ProductDetail.as_view(),
         name='product_detail'),
    path('submit_review/<int:product_id>/',
         views.submit_review,
         name='submit_review'),
    path('search/', views.ProductSearchListView.as_view(), name='search'),
    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),
    path('api/v1/latest-products/', views.LatestProductsAPIList.as_view()),
    path('api/v1/products/search/', views.search_api),
    path('api/v1/products/<slug:category_slug>/<slug:product_slug>/',
         views.ProductAPIDetail.as_view()),
    path('api/v1/products/<slug:category_slug>/',
         views.CategoryAPIDetail.as_view()),
    path('api/v1/product-categories/', views.ProductCategoryAPIView.as_view()),
]
