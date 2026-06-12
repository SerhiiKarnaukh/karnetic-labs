from core.views.portfolio import (
    CategoryDetail,
    ProjectDetail,
    ProjectSearchListView,
    ProjectsByTag,
)
from core.views.angular_api import AngularAppsAPIList, angular_search_api
from core.views.vue_api import VueAppsAPIList, search_api

__all__ = [
    'AngularAppsAPIList',
    'CategoryDetail',
    'ProjectDetail',
    'ProjectSearchListView',
    'ProjectsByTag',
    'VueAppsAPIList',
    'angular_search_api',
    'search_api',
]
