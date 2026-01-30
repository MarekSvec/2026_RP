from django.db import models
from django.contrib.auth.models import User

# Create your models here.

# Desktop System Models
class DesktopFolder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='folders')
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolders')
    created_at = models.DateTimeField(auto_now_add=True)
    x_position = models.IntegerField(default=0)  # Pro drag-and-drop
    y_position = models.IntegerField(default=0)  # Pro drag-and-drop
    
    class Meta:
        unique_together = ('user', 'parent', 'name')
    
    def __str__(self):
        return f"{self.user.username}/{self.name}"


class DesktopFile(models.Model):
    FILE_TYPES = [
        ('text', 'Text File'),
        ('image', 'Image'),
        ('document', 'Document'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('archive', 'Archive'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='files')
    folder = models.ForeignKey(DesktopFolder, on_delete=models.CASCADE, related_name='files', null=True, blank=True)
    name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FILE_TYPES, default='other')
    content = models.TextField(blank=True, null=True)  # Pro textové soubory
    file_size = models.IntegerField(default=0)  # v bytech
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    x_position = models.IntegerField(default=0)  # Pro drag-and-drop
    y_position = models.IntegerField(default=0)  # Pro drag-and-drop
    icon_color = models.CharField(max_length=7, default='#4CAF50')  # HEX barva
    
    class Meta:
        unique_together = ('user', 'folder', 'name')
    
    def __str__(self):
        return f"{self.user.username}/{self.name}"


class DesktopWindow(models.Model):
    """Sleduje otevřená okna na desktopě"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='windows')
    file = models.ForeignKey(DesktopFile, on_delete=models.CASCADE, null=True, blank=True)
    folder = models.ForeignKey(DesktopFolder, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=255)
    width = models.IntegerField(default=600)
    height = models.IntegerField(default=400)
    x_position = models.IntegerField(default=100)
    y_position = models.IntegerField(default=100)
    is_maximized = models.BooleanField(default=False)
    is_minimized = models.BooleanField(default=False)
    z_index = models.IntegerField(default=0)  # Pro vrstvení oken
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"


class War(models.Model):
    name = models.CharField(max_length=100)
    start = models.IntegerField()
    end = models.IntegerField()
    contextWar = models.TextField(default="")
    imageWar = models.URLField(default=0)
    belligerents = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Tactics(models.Model):
    description = models.TextField()

    def __str__(self):
        return self.description


class Era(models.Model):
    name = models.CharField(max_length=100)
    start = models.IntegerField()
    end = models.IntegerField()
    contextEra = models.TextField()
    imageEra = models.URLField(max_length=100)

    def __str__(self):
        return self.name


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


    def __str__(self):
        return self.title[:20]