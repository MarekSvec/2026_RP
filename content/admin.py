from django.contrib import admin

# Register your models here.
from .models import DesktopFile, DesktopFolder, DesktopWindow


@admin.register(DesktopFolder)
class DesktopFolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'parent', 'created_at')
    list_filter = ('user', 'created_at')
    search_fields = ('name', 'user__username')


@admin.register(DesktopFile)
class DesktopFileAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'file_type', 'folder', 'created_at')
    list_filter = ('user', 'file_type', 'created_at')
    search_fields = ('name', 'user__username')


@admin.register(DesktopWindow)
class DesktopWindowAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'is_maximized', 'is_minimized', 'z_index')
    list_filter = ('user', 'is_maximized', 'is_minimized')
    search_fields = ('title', 'user__username')