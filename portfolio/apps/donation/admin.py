from django.contrib import admin

from donation.models import Donation, Transaction

admin.site.register(Donation)
admin.site.register(Transaction)
