from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from ads.views import home_view  # ⬅️ ajout requis

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('ads/', include('ads.urls')),  # ✅ 1 seule déclaration avec namespace
    path('chat/', include('chat.urls')),
    path('transactions/', include('transactions.urls')),
    path('monero_app/', include('monero_app.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('support/', include('support.urls')),
    path('', home_view, name='home'),  # ✅ accès à / sans inclure deux fois ads.urls
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

