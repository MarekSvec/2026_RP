from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
import content.views

# Vytvořím router pro REST API
router = DefaultRouter()
router.register(r'api/folders', content.views.DesktopFolderViewSet, basename='folder')
router.register(r'api/files', content.views.DesktopFileViewSet, basename='file')
router.register(r'api/windows', content.views.DesktopWindowViewSet, basename='window')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', content.views.homepage),
    path('article/<int:id>/', content.views.article),
    path('context/<int:id>/', content.views.context),
    path('tactics/<str:tactics_link>/', content.views.article_tactics),
    path('era/<int:id>', content.views.era),
    
    # Desktop aplikace
    path('desktop/', content.views.desktop, name='desktop'),
    
    # REST API
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
]
