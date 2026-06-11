from django.urls import path

from social_notification.views import notifications, read_notification

app_name = 'social_notification'

urlpatterns = [
    path('', notifications, name='notifications'),
    path('read/<uuid:pk>/', read_notification, name='read_notification'),
]
