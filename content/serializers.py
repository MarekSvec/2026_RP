from rest_framework import serializers
from .models import DesktopFile, DesktopFolder, DesktopWindow


class DesktopFolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = DesktopFolder
        fields = ['id', 'name', 'parent', 'created_at', 'x_position', 'y_position']
        read_only_fields = ['created_at']


class DesktopFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DesktopFile
        fields = ['id', 'name', 'file_type', 'folder', 'content', 'file_size', 
                  'created_at', 'modified_at', 'x_position', 'y_position', 'icon_color']
        read_only_fields = ['created_at', 'modified_at', 'file_size']


class DesktopWindowSerializer(serializers.ModelSerializer):
    class Meta:
        model = DesktopWindow
        fields = ['id', 'title', 'file', 'folder', 'width', 'height', 'x_position', 
                  'y_position', 'is_maximized', 'is_minimized', 'z_index', 'created_at']
        read_only_fields = ['created_at']
