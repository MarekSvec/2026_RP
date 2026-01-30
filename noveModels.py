from django.db import models

class Article(models.Model):
    title = models.CharField(max_length=100)
    year = models.IntegerField()
    war = models.CharField(max_length=200)
    description = models.CharField(max_length=200)
    location = models.CharField(max_length=100)
    casualties = models.IntegerField(default=0)
    image = models.URLField(max_length=100)
    imageWar = models.URLField(max_length=100)
    tactics_link = models.CharField(max_length=100)
    tactics = models.TextField()
    imageTactics = models.URLField(max_length=100)
    context = models.ForeignKey(War, on_delete=models.CASCADE, related_name='articles')
    eras = models.ManyToManyField(Era, related_name='articles')
    order = models.IntegerField(default=0)