from django.apps import AppConfig
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_PRIVATE_KEY


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'taberna_orders'
    verbose_name = '07.Taberna: Orders'

    def ready(self):
        from taberna_orders.signals import paypal_taberna_payment_received
        paypal_taberna_payment_received
        self.create_tax_rate()

    def create_tax_rate(self):
        try:
            tax_rates = stripe.TaxRate.list(active=True).data
            existing_tax_rate = next((rate for rate in tax_rates if rate.display_name == "VAT"), None)
            if not existing_tax_rate:
                stripe.TaxRate.create(
                    display_name="VAT",
                    description="VAT 2%",
                    percentage=float(settings.TABERNA_TAX_RATE * 100),
                    inclusive=False
                )
        except stripe.error.StripeError as e:
            print(f"Error creating tax: {e}")
