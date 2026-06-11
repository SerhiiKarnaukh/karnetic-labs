from django.apps import AppConfig


class DonationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'donation'
    verbose_name = '09.Donation'

    def ready(self):
        from donation.signals import paypal_payment_received
        paypal_payment_received
