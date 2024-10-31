from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('ads/', include('ads.urls', namespace='ads')),
    path('transactions/', include('transactions.urls')),
    path('chat/', include('chat.urls')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('support/', include('support.urls')),  # Add support app
    path('monero/', include('monero_app.urls', namespace='monero')),  # Add monero_app for API or background tasks
    path('', include('ads.urls', namespace='ads')),  # Landing page points to ads and search ads
]
