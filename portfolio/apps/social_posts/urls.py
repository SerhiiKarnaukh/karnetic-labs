from django.urls import path

from social_posts.views import (
    get_trends,
    post_create,
    post_create_comment,
    post_delete,
    post_detail,
    post_like,
    post_list,
    post_list_profile,
    post_report,
    search,
)

app_name = 'social_posts'

urlpatterns = [
    path('', post_list, name='post_list'),
    path('<uuid:pk>/', post_detail, name='post_detail'),
    path('<uuid:pk>/like/', post_like, name='post_like'),
    path('<uuid:pk>/comment/', post_create_comment, name='post_create_comment'),
    path('<uuid:pk>/delete/', post_delete, name='post_delete'),
    path('<uuid:pk>/report/', post_report, name='post_report'),
    path('profile/<slug:slug>/', post_list_profile, name='post_list_profile'),
    path('create/', post_create, name='post_create'),
    path('search/', search, name='search'),
    path('trends/', get_trends, name='get_trends'),
]
