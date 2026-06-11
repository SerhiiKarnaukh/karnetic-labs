from django.db import models
from django.db.models import Avg, Count
from django.urls import reverse

from taberna_product.models.category import Category
from taberna_profiles.models import UserProfile


class Product(models.Model):
    category = models.ForeignKey(Category,
                                 related_name='products',
                                 on_delete=models.CASCADE)
    created_by = models.ForeignKey(UserProfile,
                                   related_name='product_creator',
                                   on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=200)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    image = models.ImageField(upload_to='store/products/',
                              blank=True,
                              null=True)
    stock = models.IntegerField()
    is_available = models.BooleanField(default=True)
    date_added = models.DateTimeField(auto_now_add=True)
    stripe_product_id = models.CharField(max_length=30, blank=True, null=True, unique=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Products'
        ordering = ('-date_added', )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.category.slug, self.slug])

    def averageReview(self):
        from taberna_product.models.review import ReviewRating
        reviews = ReviewRating.objects.filter(
            product=self, status=True).aggregate(average=Avg('rating'))
        avg = 0
        if reviews['average'] is not None:
            avg = float(reviews['average'])
        return avg

    def countReview(self):
        from taberna_product.models.review import ReviewRating
        reviews = ReviewRating.objects.filter(
            product=self, status=True).aggregate(count=Count('id'))
        count = 0
        if reviews['count'] is not None:
            count = int(reviews['count'])
        return count


class VariationManager(models.Manager):

    def colors(self):
        return super(VariationManager, self).filter(variation_category='color',
                                                    is_active=True)

    def sizes(self):
        return super(VariationManager, self).filter(variation_category='size',
                                                    is_active=True)


variation_category_choice = (
    ('color', 'color'),
    ('size', 'size'),
)


class Variation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variation_category = models.CharField(max_length=100,
                                          choices=variation_category_choice)
    variation_value = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now=True)

    objects = VariationManager()

    def __str__(self):
        return self.variation_value


class ProductGallery(models.Model):
    product = models.ForeignKey(Product,
                                related_name='productgallery',
                                default=None,
                                on_delete=models.CASCADE)
    image = models.ImageField(upload_to='store/gallery/', max_length=255)

    def __str__(self):
        return self.product.name

    class Meta:
        verbose_name = 'productgallery'
        verbose_name_plural = 'product gallery'
