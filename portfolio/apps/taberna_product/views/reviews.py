from django.contrib import messages
from django.shortcuts import redirect

from taberna_product.forms import ReviewForm
from taberna_product.models import ReviewRating


def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    user_profile = request.user.userprofile
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=user_profile.id,
                                               product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request,
                             'Thank you! Your review has been updated.')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = user_profile.id
                data.save()
                messages.success(request,
                                 'Thank you! Your review has been submitted.')
                return redirect(url)
