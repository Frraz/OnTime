"""URLs raiz do projeto OnTime."""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    # Redirect raiz
    path("", lambda request: redirect("jornada:painel")),
    
    # Admin
    path("admin/", admin.site.urls),
    
    # Apps
    path("usuarios/", include("usuarios.urls")),
    path("empresas/", include("empresas.urls")),
    path("jornada/", include("jornada.urls")),
    path("banco-horas/", include("banco_horas.urls")),
    path("fechamentos/", include("fechamentos.urls")),
    path("auditoria/", include("auditoria.urls")),
    
    # Arquivos estáticos (produção)
    path("estaticos/<path:path>", serve, {"document_root": settings.STATIC_ROOT}),
]

# Arquivos de mídia (uploads de fotos)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)