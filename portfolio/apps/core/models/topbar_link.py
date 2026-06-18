from django.db import models


class TopbarLink(models.Model):
    class Key(models.TextChoices):
        CV = 'cv', 'CV'
        GITHUB = 'github', 'GitHub'
        LINKEDIN = 'linkedin', 'LinkedIn'

    key = models.CharField(max_length=20, choices=Key.choices, unique=True)
    url = models.URLField(blank=True, default='')
    title = models.CharField(max_length=100)
    icon_class = models.CharField(max_length=100)
    ordering = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'key']
        verbose_name = 'Topbar link'
        verbose_name_plural = 'Topbar links'

    def __str__(self):
        return self.title
