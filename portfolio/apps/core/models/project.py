from django.db import models
from django.urls import reverse

from core.models.taxonomy import Category, Tag


class Project(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    photo = models.ImageField(upload_to='portfolio/projects/', blank=True)
    github_url = models.URLField(max_length=200)
    view_url = models.URLField(max_length=200, blank=True)
    slug = models.SlugField(max_length=255, verbose_name='Slug', unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='projects',
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='projects')
    ordering = models.PositiveIntegerField(default=0, verbose_name="Ordering")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            'core:project_detail',
            args=[self.category.slug, self.slug],
        )

    class Meta:
        verbose_name_plural = 'Projects'
        ordering = ['-created_at']


class ProjectGallery(models.Model):
    project = models.ForeignKey(
        Project,
        related_name='projectgallery',
        default=None,
        on_delete=models.CASCADE,
    )
    image = models.ImageField(
        upload_to='portfolio/project_gallery/',
        max_length=255,
    )

    def __str__(self):
        return self.project.title

    class Meta:
        verbose_name = 'projectgallery'
        verbose_name_plural = 'project gallery'
