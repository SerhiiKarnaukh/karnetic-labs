from django.urls import path

from . import api

app_name = 'social_profiles'

urlpatterns = [
    path(
        'api/v1/token/',
        api.SocialTokenObtainPairView.as_view(),
        name='social-token-obtain-pair',
    ),
    path('register/', api.SocialProfileCreateView.as_view(), name='user-register'),
    path('editprofile/', api.editprofile, name='editprofile'),
    path('editpassword/', api.editpassword, name='editpassword'),
    path('friends/suggested/', api.my_friendship_suggestions, name='my_friendship_suggestions'),
    path('friends/<slug:slug>/', api.friends, name='friends'),
    path('friends/<slug:slug>/request/',
         api.send_friendship_request,
         name='send_friendship_request'),
    path('friends/<slug:slug>/<str:status>/',
         api.handle_request,
         name='handle_request'),
    path('me/', api.me, name='me'),
]
