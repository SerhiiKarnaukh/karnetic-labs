from random import choice

from django.conf import settings
from django.dispatch import receiver
from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received

from donation.models import Donation, Transaction


@receiver(valid_ipn_received)
def paypal_payment_received(sender, **kwargs):
    ipn_obj = sender

    if ipn_obj.payment_status == ST_PP_COMPLETED:
        if ipn_obj.receiver_email != settings.PAYPAL_RECEIVER_EMAIL:
            return

        try:
            myDonation = choice(Donation.objects.all())
            assert ipn_obj.mc_gross == myDonation.amount and ipn_obj.mc_currency == 'USD'
        except Exception:
            print('Paypal ipn object data is invalid!')
        else:
            Transaction.objects.create(
                invoice=ipn_obj.invoice,
                title=ipn_obj.item_name,
                amount=ipn_obj.mc_gross,
                paid=True,
            )
    else:
        print('Paypal payment status not completed: %s' % ipn_obj.payment_status)
