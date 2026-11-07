from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.home),
    path('admin/', admin.site.urls),
    path('api/', views.api_index),
    path('api/', include('accounts.urls')),
    path('api/', include('scraper.urls')),
    path('api/', include('voitures.urls')),
]

# Servir les fichiers media (photos des voitures) en mode dev
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
