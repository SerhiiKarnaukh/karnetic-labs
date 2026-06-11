from social_profiles.views.auth import SocialTokenObtainPairView
from social_profiles.views.friendship import (
    friends,
    handle_request,
    my_friendship_suggestions,
    send_friendship_request,
)
from social_profiles.views.profile import editpassword, editprofile, me
from social_profiles.views.registration import SocialProfileCreateView

__all__ = [
    'SocialProfileCreateView',
    'SocialTokenObtainPairView',
    'editpassword',
    'editprofile',
    'friends',
    'handle_request',
    'me',
    'my_friendship_suggestions',
    'send_friendship_request',
]
