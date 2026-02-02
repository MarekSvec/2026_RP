from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
import content.views

# Vytvořím router pro REST API
router = DefaultRouter()
router.register(r'api/folders', content.views.DesktopFolderViewSet, basename='folder')
router.register(r'api/files', content.views.DesktopFileViewSet, basename='file')
router.register(r'api/windows', content.views.DesktopWindowViewSet, basename='window')
router.register(r'api/messages', content.views.MessageViewSet, basename='message')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', content.views.desktop, name='desktop'),
    path('login/', content.views.login_view, name='login'),
    path('register/', content.views.register_view, name='register'),
    path('logout/', content.views.logout_view, name='logout'),
    
    # Google OAuth
    path('accounts/', include('allauth.urls')),
    
    # REST API
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
]
