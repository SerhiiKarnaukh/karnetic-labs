from django.views.generic import ListView, DetailView
from django.shortcuts import redirect, render
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib import messages

from .models import Product, Category, ReviewRating, ProductGallery

from .forms import ReviewForm


class FrontPage(ListView):
    model = Product
    template_name = 'taberna_store/frontpage.html'
    context_object_name = 'products'

    def get_queryset(self):
        return Product.objects.all().filter(
            is_available=True).select_related('category')[0:6]


def contact(request):
    return render(request, 'taberna_store/contact.html')


def about(request):
    return render(request, 'taberna_store/about.html')


class ProductDetail(DetailView):
    model = Product
    template_name = 'taberna_product/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        category = product.category

        related_products = Product.objects.filter(
            category=category).exclude(id=product.id)

        related_products_paginator = Paginator(related_products, 3)
        related_products_chunks = []
        for page in related_products_paginator.page_range:
            current_page = related_products_paginator.get_page(page)
            related_products_chunks.append(current_page.object_list)

        context['related_products'] = related_products
        context['related_products_chunks'] = related_products_chunks

        context['reviews'] = ReviewRating.objects.filter(
            product__slug=product.slug, status=True)

        all_gallery_images = ProductGallery.objects.filter(product=product)
        gallery_paginator = Paginator(all_gallery_images, 3)
        all_gallery_images_list = []
        for page in gallery_paginator.page_range:
            current_page = gallery_paginator.get_page(page)
            all_gallery_images_list.append(current_page.object_list)
        context['product_gallery'] = all_gallery_images_list

        return context


class CategoryDetail(ListView):
    paginate_by = 6
    model = Product
    template_name = 'taberna_product/store.html'
    context_object_name = 'products'
    allow_empty = False

    def create_store_data(self, **kwargs):
        context = kwargs
        if 'slug' in self.kwargs:
            context['store_title'] = str(
                Category.objects.get(slug=self.kwargs['slug']))
            context['product_count'] = Product.objects.filter(
                category__slug=self.kwargs['slug'], is_available=True).count()
            return context
        else:
            context['store_title'] = 'All products'
            context['product_count'] = Product.objects.all().filter(
                is_available=True).count()
            return context

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.create_store_data()
        return dict(list(context.items()) + list(c_def.items()))

    def get_queryset(self, **kwargs):
        if 'slug' in self.kwargs:
            return Product.objects.filter(
                category__slug=self.kwargs['slug'],
                is_available=True).select_related('category')
        else:
            return Product.objects.all().filter(
                is_available=True).select_related('category')


class ProductSearchListView(ListView):
    model = Product
    template_name = 'taberna_product/store.html'
    context_object_name = 'products'
    paginate_by = 4

    def get_queryset(self):
        query = self.request.GET.get('keyword')
        if query:
            return Product.objects.filter(
                Q(description__icontains=query)
                | Q(name__icontains=query)).order_by('-date_added')
        return Product.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product_count'] = self.get_queryset().count()
        context['store_title'] = 'Search Result'
        return context


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
