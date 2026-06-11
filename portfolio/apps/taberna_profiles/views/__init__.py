from taberna_profiles.views.api import (
    CustomTokenObtainPairView,
    TabernaProfileCreateView,
    UserOrdersListView,
)
from taberna_profiles.views.auth import (
    activate,
    activate_result,
    change_password,
    forgotPassword,
    login,
    logout,
    register,
    resetPassword,
    resetpassword_validate,
)
from taberna_profiles.views.dashboard import (
    dashboard,
    edit_profile,
    my_orders,
    order_detail,
)

__all__ = [
    'CustomTokenObtainPairView',
    'TabernaProfileCreateView',
    'UserOrdersListView',
    'activate',
    'activate_result',
    'change_password',
    'dashboard',
    'edit_profile',
    'forgotPassword',
    'login',
    'logout',
    'my_orders',
    'order_detail',
    'register',
    'resetPassword',
    'resetpassword_validate',
]
