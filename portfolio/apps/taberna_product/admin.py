from django.contrib import admin
import admin_thumbnails

from taberna_product.models import Category, Product, ProductGallery, ReviewRating, Variation


@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1


class CategoryAdminModel(admin.ModelAdmin):
    list_display = (
        'name',
        'slug',
        'ordering',
    )
    list_display_links = ('name', )
    search_fields = ('name', )
    list_editable = ('ordering', )
    prepopulated_fields = {"slug": ("name", )}


class VariationAdminInline(admin.TabularInline):
    model = Variation
    extra = 1


class ProductAdminModel(admin.ModelAdmin):
    list_display = (
        'name',
        'category',
        'price',
        'is_available',
        'stock',
        'date_added',
        'image',
    )
    list_display_links = ('name', )
    search_fields = (
        'name',
        'description',
    )
    list_editable = (
        'is_available',
        'stock',
        'price',
    )
    list_filter = (
        'is_available',
        'date_added',
        'category',
    )
    prepopulated_fields = {"slug": ("name", )}
    inlines = [ProductGalleryInline, VariationAdminInline]


admin.site.register(Category, CategoryAdminModel)
admin.site.register(Product, ProductAdminModel)
admin.site.register(ReviewRating)
admin.site.register(ProductGallery)
