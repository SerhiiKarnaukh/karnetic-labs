from django.contrib import admin
from django import forms
from django.utils.safestring import mark_safe
from django.utils.html import format_html

from django_ckeditor_5.widgets import CKEditor5Widget
import admin_thumbnails


from .models import Category, Tag, Project, ProjectGallery, ServerStatistics


ERROR_PREFIX = ServerStatistics.ERROR_PREFIX


def _colored_field(value):
    """Render value in red if it starts with N/A, green otherwise."""
    if str(value).startswith(ERROR_PREFIX):
        return format_html('<span style="color:#ba2121;">{}</span>', value)
    return format_html('<span style="color:#28a745;">{}</span>', value)


@admin_thumbnails.thumbnail('image')
class ProjectGalleryInline(admin.TabularInline):
    model = ProjectGallery
    extra = 1


class ProjectAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["content"].required = False

    class Meta:
        model = Project
        fields = '__all__'
        widgets = {
            "content": CKEditor5Widget(
                attrs={"class": "django_ckeditor_5"}, config_name="extends"
            )
        }


class ProjectAdmin(admin.ModelAdmin):
    save_on_top = True
    form = ProjectAdminForm
    list_display = (
        'id',
        'title',
        'ordering',
        'slug',
        # 'tags',
        'category',
        'created_at',
        'get_photo',
    )
    list_editable = ('ordering',)
    list_display_links = (
        'id',
        'title',
    )
    search_fields = (
        'title',
        'content',
    )
    list_filter = (
        'created_at',
        'category',
        'tags',
    )
    readonly_fields = (
        'created_at',
        'get_photo',
    )
    fields = (
        'title',
        'ordering',
        'slug',
        'category',
        'tags',
        'content',
        'github_url',
        'view_url',
        'photo',
        'get_photo',
        'created_at',
    )
    ordering = ['ordering', '-created_at']
    prepopulated_fields = {"slug": ("title", )}
    inlines = [ProjectGalleryInline]

    def get_photo(self, obj):
        if obj.photo:
            return mark_safe(f'<img src="{obj.photo.url}" width="300">')
        return '-'

    get_photo.short_description = 'Image'


class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title", )}


class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title", )}


@admin.register(ServerStatistics)
class ServerStatisticsAdmin(admin.ModelAdmin):
    list_display = (
        'collected_at',
        'app_version',
        'colored_db_size',
        'colored_media_size',
        'colored_disk_total',
        'colored_disk_used',
        'colored_disk_available',
    )
    list_filter = ('app_version',)
    ordering = ('-collected_at',)

    @admin.display(description='DB Size')
    def colored_db_size(self, obj):
        return _colored_field(obj.db_size)

    @admin.display(description='Media Size')
    def colored_media_size(self, obj):
        return _colored_field(obj.media_size)

    @admin.display(description='Disk Total')
    def colored_disk_total(self, obj):
        return _colored_field(obj.disk_total)

    @admin.display(description='Disk Used')
    def colored_disk_used(self, obj):
        return _colored_field(obj.disk_used)

    @admin.display(description='Disk Available')
    def colored_disk_available(self, obj):
        return _colored_field(obj.disk_available)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True


admin.site.register(Category, CategoryAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Project, ProjectAdmin)
