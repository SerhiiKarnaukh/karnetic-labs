from django.db import models


class Trend(models.Model):
    hashtag = models.CharField(max_length=255)
    occurences = models.IntegerField()
