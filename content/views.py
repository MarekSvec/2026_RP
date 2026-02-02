from django.shortcuts import render, redirect
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import DesktopFile, DesktopFolder, DesktopWindow, Message, MessageAttachment
from .serializers import DesktopFileSerializer, DesktopFolderSerializer, DesktopWindowSerializer, MessageSerializer


# ===== HELPER FUNCTIONS =====
def get_unique_name(name, user, folder=None, item_type='file'):
    """Vygeneruje unikátní název souboru/složky v zadané poloze"""
    if item_type == 'file':
        # Nejdříve kontrola zda soubor se STEJNÝM jménem existuje
        existing = DesktopFile.objects.filter(user=user, folder=folder, name=name).exists()
        if not existing:
            return name
        
        # Najít dostupné číslo
        base_name = name.rsplit('.', 1)[0] if '.' in name else name
        ext = '.' + name.rsplit('.', 1)[1] if '.' in name else ''
        counter = 1
        while True:
            new_name = f"{base_name} ({counter}){ext}"
            if not DesktopFile.objects.filter(user=user, folder=folder, name=new_name).exists():
                return new_name
            counter += 1
    
    elif item_type == 'folder':
        # Nejdříve kontrola zda složka se STEJNÝM jménem existuje
        existing = DesktopFolder.objects.filter(user=user, parent=folder, name=name).exists()
        if not existing:
            return name
        
        # Najít dostupné číslo
        counter = 1
        while True:
            new_name = f"{name} ({counter})"
            if not DesktopFolder.objects.filter(user=user, parent=folder, name=new_name).exists():
                return new_name
            counter += 1
    
    return name


def get_unique_name_with_base_check(name, user, item_type='file'):
    """Vygeneruje unikátní název se kontrolou na kolize ZÁKLADNÍHO jména na celém desktopu"""
    if item_type == 'file':
        # Extrahovat základní jméno
        base_name = name.rsplit('.', 1)[0] if '.' in name else name
        ext = '.' + name.rsplit('.', 1)[1] if '.' in name else ''
        
        # Najít všechny soubory na desktopu (bez složky) se stejným základem
        existing_files = DesktopFile.objects.filter(
            user=user, 
            folder__isnull=True,
            name__startswith=base_name
        )
        
        # Pokud se původní jméno nepoužívá, vrátit ho
        if not DesktopFile.objects.filter(user=user, folder__isnull=True, name=name).exists():
            # Ale zkontrolovat aby se necollidovalo s existujícím základem
            if not existing_files.exists():
                return name
        
        # Najít dostupné číslo
        counter = 1
        while True:
            new_name = f"{base_name} ({counter}){ext}"
            if not DesktopFile.objects.filter(user=user, folder__isnull=True, name=new_name).exists():
                return new_name
            counter += 1
    
    elif item_type == 'folder':
        # Kontoluje kolize na desktopu (bez rodičovské složky)
        existing = DesktopFolder.objects.filter(user=user, parent__isnull=True, name=name).exists()
        if not existing:
            return name
        
        # Najít dostupné číslo
        counter = 1
        while True:
            new_name = f"{name} ({counter})"
            if not DesktopFolder.objects.filter(user=user, parent__isnull=True, name=new_name).exists():
                return new_name
            counter += 1
    
    return name


def get_unique_name_global(name, user, item_type='file'):
    """Vygeneruje unikátní název se kontrolou na kolize VŠECH souborů/složek uživatele (globální kontrola)"""
    if item_type == 'file':
        # Extrahovat základní jméno
        base_name = name.rsplit('.', 1)[0] if '.' in name else name
        ext = '.' + name.rsplit('.', 1)[1] if '.' in name else ''
        
        # Kontrola zda se již používá přesně toto jméno KDEKOLI
        if not DesktopFile.objects.filter(user=user, name=name).exists():
            return name
        
        # Najít dostupné číslo - kontrola proti VŠEM souborům uživatele
        counter = 1
        while True:
            new_name = f"{base_name} ({counter}){ext}"
            if not DesktopFile.objects.filter(user=user, name=new_name).exists():
                return new_name
            counter += 1
    
    elif item_type == 'folder':
        # Kontrola zda se již používá přesně toto jméno KDEKOLI
        if not DesktopFolder.objects.filter(user=user, name=name).exists():
            return name
        
        # Najít dostupné číslo - kontrola proti VŠEM složkám uživatele
        counter = 1
        while True:
            new_name = f"{name} ({counter})"
            if not DesktopFolder.objects.filter(user=user, name=new_name).exists():
                return new_name
            counter += 1
    
    return name


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
    
    @action(detail=False, methods=['get'])
    def all_files(self, request):
        """Vrací VŠECHNY soubory uživatele (včetně těch ve složkách) - pro attachment selector"""
        files = DesktopFile.objects.filter(user=request.user)
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


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Vrací zprávy poslane nebo přijaté aktuálním uživatelem
        user = self.request.user
        return Message.objects.filter(
            models.Q(sender=user) | models.Q(recipients=user)
        ).prefetch_related('attachments', 'attachments__file', 'attachments__folder').distinct().order_by('-created_at')
    
    def retrieve(self, request, *args, **kwargs):
        """Vrací jednu zprávu s přílohami"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Vytvoří novou zprávu"""
        try:
            recipients_usernames = request.data.get('recipients', [])
            subject = request.data.get('subject')
            body = request.data.get('body')
            attachments_data = request.data.get('attachments', [])
            
            print(f"DEBUG: Creating message with attachments_data: {attachments_data}")
            
            if not recipients_usernames or not subject or not body:
                return Response(
                    {'error': 'Recipients, subject and body are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Převedeme uživatelská jména na User objekty
            recipients = []
            for username in recipients_usernames:
                try:
                    user = User.objects.get(username=username.strip())
                    recipients.append(user)
                except User.DoesNotExist:
                    return Response(
                        {'error': f'User {username} not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            
            # Vytvoříme zprávu
            message = Message.objects.create(
                sender=request.user,
                subject=subject,
                body=body
            )
            message.recipients.set(recipients)
            
            # Přidáme přílohy
            print(f"DEBUG: Processing {len(attachments_data)} attachments")
            for attachment_data in attachments_data:
                attachment_type = attachment_data.get('type')
                attachment_id = attachment_data.get('id')
                
                print(f"DEBUG: Processing attachment - type: {attachment_type}, id: {attachment_id}")
                
                if attachment_type == 'file' and attachment_id:
                    try:
                        file = DesktopFile.objects.get(id=attachment_id, user=request.user)
                        att = MessageAttachment.objects.create(message=message, file=file)
                        print(f"DEBUG: Created attachment {att.id} for file {file.id}")
                    except DesktopFile.DoesNotExist:
                        print(f"DEBUG: File not found: {attachment_id}")
                        pass
                elif attachment_type == 'folder' and attachment_id:
                    try:
                        folder = DesktopFolder.objects.get(id=attachment_id, user=request.user)
                        att = MessageAttachment.objects.create(message=message, folder=folder)
                        print(f"DEBUG: Created attachment {att.id} for folder {folder.id}")
                    except DesktopFolder.DoesNotExist:
                        print(f"DEBUG: Folder not found: {attachment_id}")
                        pass
            
            # Přenačti zprávu s attachments
            message = Message.objects.prefetch_related('attachments', 'attachments__file', 'attachments__folder').get(id=message.id)
            print(f"DEBUG: Final message has {message.attachments.count()} attachments")
            serializer = self.get_serializer(message)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def inbox(self, request):
        """Vrací přijaté zprávy"""
        messages = self.get_queryset().filter(recipients=request.user)
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def sent(self, request):
        """Vrací poslane zprávy"""
        messages = self.get_queryset().filter(sender=request.user)
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Označí zprávu jako přečtenou"""
        try:
            message = Message.objects.get(id=pk, recipients=request.user)
            message.is_read = True
            message.save()
            serializer = self.get_serializer(message)
            return Response(serializer.data)
        except Message.DoesNotExist:
            return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def copy_attachment(self, request, pk=None):
        """Kopíruje attachment do desktopového prostředí aktuálního uživatele"""
        try:
            print(f"DEBUG copy_attachment: pk={pk}, request.data={request.data}")
            
            message = Message.objects.get(id=pk)
            # Zkontrolovat že si zprávu může přečíst
            if message.sender != request.user and request.user not in message.recipients.all():
                return Response({'error': 'Nemáte přístup k této zprávě'}, status=status.HTTP_403_FORBIDDEN)
            
            attachment_id = request.data.get('attachment_id')
            attachment_type = request.data.get('type')  # 'file' nebo 'folder'
            x_pos = request.data.get('x_position', 0)
            y_pos = request.data.get('y_position', 0)
            
            print(f"DEBUG: attachment_id={attachment_id}, attachment_type={attachment_type}")
            
            if not attachment_id or not attachment_type:
                print(f"DEBUG: Chybí attachment_id nebo type")
                return Response({'error': 'Chybí attachment_id nebo type'}, status=status.HTTP_400_BAD_REQUEST)
            
            if attachment_type == 'file':
                try:
                    original_file = DesktopFile.objects.get(id=attachment_id)
                    # Přidat informaci od koho přišel soubor
                    file_name = original_file.name
                    base_name = file_name.rsplit('.', 1)[0] if '.' in file_name else file_name
                    ext = '.' + file_name.rsplit('.', 1)[1] if '.' in file_name else ''
                    name_with_sender = f"{base_name} (od {message.sender.username}){ext}"
                    
                    # Vygenerovat unikátní název se kontrolou na desktopu
                    unique_name = get_unique_name_with_base_check(name_with_sender, request.user, item_type='file')
                    # Vytvořit kopii pro aktuálního uživatele
                    new_file = DesktopFile.objects.create(
                        user=request.user,
                        name=unique_name,
                        file_type=original_file.file_type,
                        content=original_file.content,
                        file_size=original_file.file_size,
                        x_position=x_pos,
                        y_position=y_pos,
                        icon_color=original_file.icon_color
                    )
                    return Response({
                        'success': True,
                        'file': DesktopFileSerializer(new_file).data
                    })
                except DesktopFile.DoesNotExist:
                    return Response({'error': 'Soubor nebyl nalezen'}, status=status.HTTP_404_NOT_FOUND)
            
            elif attachment_type == 'folder':
                try:
                    original_folder = DesktopFolder.objects.get(id=attachment_id)
                    # Přidat informaci od koho přišla složka
                    folder_name_with_sender = f"{original_folder.name} (od {message.sender.username})"
                    # Vygenerovat unikátní název se kontrolou na desktopu
                    unique_name = get_unique_name_with_base_check(folder_name_with_sender, request.user, item_type='folder')
                    # Vytvořit kopii pro aktuálního uživatele
                    new_folder = DesktopFolder.objects.create(
                        user=request.user,
                        name=unique_name,
                        x_position=x_pos,
                        y_position=y_pos
                    )
                    
                    # Zkopírovat všechny soubory z původní složky
                    original_files = DesktopFile.objects.filter(folder=original_folder)
                    for original_file in original_files:
                        # GLOBÁLNÍ kontrola kolizí - kontroluje proti VŠEM souborům na desktopu a ve všech složkách
                        unique_file_name = get_unique_name_global(original_file.name, request.user, item_type='file')
                        DesktopFile.objects.create(
                            user=request.user,
                            folder=new_folder,
                            name=unique_file_name,
                            file_type=original_file.file_type,
                            content=original_file.content,
                            file_size=original_file.file_size,
                            icon_color=original_file.icon_color
                        )
                    
                    return Response({
                        'success': True,
                        'folder': DesktopFolderSerializer(new_folder).data
                    })
                except DesktopFolder.DoesNotExist:
                    return Response({'error': 'Složka nebyla nalezena'}, status=status.HTTP_404_NOT_FOUND)
            
            return Response({'error': 'Neznámý typ attachmentu'}, status=status.HTTP_400_BAD_REQUEST)
        
        except Message.DoesNotExist:
            return Response({'error': 'Zpráva nebyla nalezena'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)