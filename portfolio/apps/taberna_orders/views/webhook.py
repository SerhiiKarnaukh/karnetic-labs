from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from taberna_orders.webhooks.stripe import handle_stripe_webhook


@require_POST
@csrf_exempt
def stripe_webhook(request):
    return handle_stripe_webhook(request)
