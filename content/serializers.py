from rest_framework import serializers
from .models import DesktopFile, DesktopFolder, DesktopWindow, Message, MessageAttachment


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


class MessageAttachmentSerializer(serializers.ModelSerializer):
    file_name = serializers.CharField(source='file.name', read_only=True, allow_null=True)
    folder_name = serializers.CharField(source='folder.name', read_only=True, allow_null=True)
    file_type = serializers.CharField(source='file.file_type', read_only=True, allow_null=True)
    
    class Meta:
        model = MessageAttachment
        fields = ['id', 'file', 'file_name', 'file_type', 'folder', 'folder_name']


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    recipients_usernames = serializers.SerializerMethodField()
    attachments = MessageAttachmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'sender_username', 'recipients', 'recipients_usernames', 
                  'subject', 'body', 'created_at', 'is_read', 'attachments']
        read_only_fields = ['sender', 'created_at']
    
    def get_recipients_usernames(self, obj):
        return [user.username for user in obj.recipients.all()]
