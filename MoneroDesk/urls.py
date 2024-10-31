from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('ads/', include('ads.urls')),
    path('transactions/', include('transactions.urls')),
    path('chat/', include('chat.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('support/', include('support.urls')),  # Add support app
    path('monero/', include('monero_app.urls')),  # Add monero_app for API or background tasks
    path('', include('ads.urls')),  # Landing page points to ads and search ads
]
