from django.db import models
from django.template.defaultfilters import slugify

from accounts.models import Account
from social_profiles.utils import get_random_code


class Profile(models.Model):
    first_name = models.CharField(max_length=200, blank=True)
    last_name = models.CharField(max_length=200, blank=True)
    username = models.CharField(max_length=50, unique=True)
    user = models.OneToOneField(Account, on_delete=models.CASCADE)
    bio = models.TextField(default="no bio...", max_length=300)
    email = models.EmailField(max_length=200, blank=True)
    country = models.CharField(max_length=200, blank=True)
    avatar = models.ImageField(upload_to='social/avatars/')
    friends = models.ManyToManyField('self', default=None)
    friends_count = models.IntegerField(default=0)
    people_you_may_know = models.ManyToManyField('self')
    posts_count = models.IntegerField(default=0)
    slug = models.SlugField(unique=True, blank=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        return f"{self.user.username}-{self.created.strftime('%d-%m-%Y')}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            account_instance = self.user
            account_fields_updated = False
            if self.first_name != account_instance.first_name:
                account_instance.first_name = self.first_name
                account_fields_updated = True
            if self.last_name != account_instance.last_name:
                account_instance.last_name = self.last_name
                account_fields_updated = True
            if self.email != account_instance.email:
                account_instance.email = self.email
                account_fields_updated = True
            if self.username != account_instance.username:
                account_instance.username = self.username

            if account_fields_updated:
                account_instance.save()

        if self.first_name == "":
            self.first_name = self.user.first_name
        if self.last_name == "":
            self.last_name = self.user.last_name
        if self.email == "":
            self.email = self.user.email
        if self.username == "":
            self.username = self.user.username

        if self.pk is None:
            self.create_slug()
        else:
            old_instance = Profile.objects.get(pk=self.pk)
            if (self.first_name != old_instance.first_name
                    or self.last_name != old_instance.last_name):
                self.create_slug()
        super().save(*args, **kwargs)

    def create_slug(self):
        if self.first_name and self.last_name:
            to_slug = slugify(f"{self.first_name}-{self.last_name}")
            ex = Profile.objects.filter(slug=to_slug).exists()
            while ex:
                to_slug = slugify(f"{to_slug}-{get_random_code()}")
                ex = Profile.objects.filter(slug=to_slug).exists()
        else:
            to_slug = str(self.user.username)
        self.slug = to_slug
