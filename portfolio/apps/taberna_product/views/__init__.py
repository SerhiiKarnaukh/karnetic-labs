from taberna_product.views.api.categories import CategoryAPIDetail, ProductCategoryAPIView
from taberna_product.views.api.products import (
    LatestProductsAPIList,
    ProductAPIDetail,
    search_api,
)
from taberna_product.views.reviews import submit_review
from taberna_product.views.storefront import (
    CategoryDetail,
    FrontPage,
    ProductDetail,
    ProductSearchListView,
    about,
    contact,
)

__all__ = [
    'CategoryAPIDetail',
    'CategoryDetail',
    'FrontPage',
    'LatestProductsAPIList',
    'ProductAPIDetail',
    'ProductCategoryAPIView',
    'ProductDetail',
    'ProductSearchListView',
    'about',
    'contact',
    'search_api',
    'submit_review',
]
