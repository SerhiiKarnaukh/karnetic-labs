from django.contrib import admin

from taberna_profiles.models import UserProfile

# Register your models here.


class UserProfileAdmin(admin.ModelAdmin):

    list_display = ('user', 'city', 'state', 'country')
    list_display_links = ('user', )


admin.site.register(UserProfile, UserProfileAdmin)
