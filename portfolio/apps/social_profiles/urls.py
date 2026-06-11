from django.urls import path

from social_profiles.views import (
    SocialProfileCreateView,
    SocialTokenObtainPairView,
    editpassword,
    editprofile,
    friends,
    handle_request,
    me,
    my_friendship_suggestions,
    send_friendship_request,
)

app_name = 'social_profiles'

urlpatterns = [
    path(
        'api/v1/token/',
        SocialTokenObtainPairView.as_view(),
        name='social-token-obtain-pair',
    ),
    path('register/', SocialProfileCreateView.as_view(), name='user-register'),
    path('editprofile/', editprofile, name='editprofile'),
    path('editpassword/', editpassword, name='editpassword'),
    path(
        'friends/suggested/',
        my_friendship_suggestions,
        name='my_friendship_suggestions',
    ),
    path('friends/<slug:slug>/', friends, name='friends'),
    path(
        'friends/<slug:slug>/request/',
        send_friendship_request,
        name='send_friendship_request',
    ),
    path(
        'friends/<slug:slug>/<str:status>/',
        handle_request,
        name='handle_request',
    ),
    path('me/', me, name='me'),
]
