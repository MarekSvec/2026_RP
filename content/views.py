from django.shortcuts import render, redirect
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import DesktopFile, DesktopFolder, DesktopWindow
from .serializers import DesktopFileSerializer, DesktopFolderSerializer, DesktopWindowSerializer


# ===== AUTHENTICATION VIEWS =====
def login_view(request):
    """Přihlášení uživatele"""
    if request.user.is_authenticated:
        return redirect('desktop')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('desktop')
        else:
            return render(request, 'content/login.html', {
                'login_error': 'Nesprávné uživatelské jméno nebo heslo'
            })
    
    return render(request, 'content/login.html')


def register_view(request):
    """Registrace nového uživatele"""
    if request.user.is_authenticated:
        return redirect('desktop')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        errors = []
        
        # Validace
        if not username or not email or not password or not password_confirm:
            errors.append('Všechna pole jsou povinná')
        elif password != password_confirm:
            errors.append('Hesla se neshodují')
        elif len(password) < 6:
            errors.append('Heslo musí mít alespoň 6 znaků')
        elif User.objects.filter(username=username).exists():
            errors.append('Toto uživatelské jméno již existuje')
        elif User.objects.filter(email=email).exists():
            errors.append('Tento email již existuje')
        
        if errors:
            return render(request, 'content/login.html', {
                'signup_errors': errors
            })
        
        # Vytvoření uživatele
        user = User.objects.create_user(username=username, email=email, password=password)
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        return redirect('desktop')
    
    return render(request, 'content/login.html')


def logout_view(request):
    """Odhlášení uživatele"""
    logout(request)
    return redirect('login')
    
    return render(request, 'content/login.html')


# ===== DESKTOP APP VIEWS =====
def desktop(request):
    """Renderuje hlavní desktop stránku"""
    if not request.user.is_authenticated:
        return render(request, 'content/login.html')
    return render(request, 'content/desktop.html')


# ===== REST API VIEWSETS =====
class DesktopFolderViewSet(viewsets.ModelViewSet):
    serializer_class = DesktopFolderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return DesktopFolder.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def root_folders(self, request):
        """Vrací složky bez rodiče (na desktopě)"""
        folders = DesktopFolder.objects.filter(user=request.user, parent__isnull=True)
        serializer = self.get_serializer(folders, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def contents(self, request, pk=None):
        """Vrací obsah složky (podsložky a soubory)"""
        try:
            folder = DesktopFolder.objects.get(id=pk, user=request.user)
        except DesktopFolder.DoesNotExist:
            return Response({'error': 'Folder not found'}, status=status.HTTP_404_NOT_FOUND)
        
        subfolders = folder.subfolders.all()
        files = folder.files.all()
        
        folder_serializer = DesktopFolderSerializer(subfolders, many=True)
        file_serializer = DesktopFileSerializer(files, many=True)
        
        return Response({
            'folders': folder_serializer.data,
            'files': file_serializer.data
        })


class DesktopFileViewSet(viewsets.ModelViewSet):
    serializer_class = DesktopFileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return DesktopFile.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def desktop_files(self, request):
        """Vrací soubory na desktopě (bez rodičovské složky)"""
        files = DesktopFile.objects.filter(user=request.user, folder__isnull=True)
        serializer = self.get_serializer(files, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def rename(self, request, pk=None):
        """Přejmenuje soubor"""
        try:
            file = DesktopFile.objects.get(id=pk, user=request.user)
            new_name = request.data.get('name')
            if new_name:
                file.name = new_name
                file.save()
                serializer = self.get_serializer(file)
                return Response(serializer.data)
            return Response({'error': 'Name required'}, status=status.HTTP_400_BAD_REQUEST)
        except DesktopFile.DoesNotExist:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def update_position(self, request, pk=None):
        """Aktualizuje pozici souboru na desktopě"""
        try:
            file = DesktopFile.objects.get(id=pk, user=request.user)
            file.x_position = request.data.get('x_position', file.x_position)
            file.y_position = request.data.get('y_position', file.y_position)
            file.save()
            serializer = self.get_serializer(file)
            return Response(serializer.data)
        except DesktopFile.DoesNotExist:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)


class DesktopWindowViewSet(viewsets.ModelViewSet):
    serializer_class = DesktopWindowSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return DesktopWindow.objects.filter(user=self.request.user).order_by('z_index')
    
    def perform_create(self, serializer):
        # Nastaví z_index na nejvyšší hodnotu + 1
        max_z_index = DesktopWindow.objects.filter(user=self.request.user).aggregate(
            max_z=models.Max('z_index')
        )['max_z'] or 0
        serializer.save(user=self.request.user, z_index=max_z_index + 1)
    
    @action(detail=True, methods=['post'])
    def update_position(self, request, pk=None):
        """Aktualizuje pozici a velikost okna"""
        try:
            window = DesktopWindow.objects.get(id=pk, user=request.user)
            window.x_position = request.data.get('x_position', window.x_position)
            window.y_position = request.data.get('y_position', window.y_position)
            window.width = request.data.get('width', window.width)
            window.height = request.data.get('height', window.height)
            window.is_maximized = request.data.get('is_maximized', window.is_maximized)
            window.is_minimized = request.data.get('is_minimized', window.is_minimized)
            window.save()
            serializer = self.get_serializer(window)
            return Response(serializer.data)
        except DesktopWindow.DoesNotExist:
            return Response({'error': 'Window not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def bring_to_front(self, request, pk=None):
        """Přesune okno na přední plán"""
        try:
            window = DesktopWindow.objects.get(id=pk, user=request.user)
            max_z_index = DesktopWindow.objects.filter(user=request.user).aggregate(
                max_z=models.Max('z_index')
            )['max_z'] or 0
            window.z_index = max_z_index + 1
            window.save()
            serializer = self.get_serializer(window)
            return Response(serializer.data)
        except DesktopWindow.DoesNotExist:
            return Response({'error': 'Window not found'}, status=status.HTTP_404_NOT_FOUND)