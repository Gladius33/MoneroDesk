from django.contrib import admin
from .models import Ad

class AdAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'crypto_currency', 'fiat_currency', 'price', 'user', 'active', 'created_at')
    list_filter = ('type', 'crypto_currency', 'fiat_currency', 'active', 'created_at')  # Filtres latéraux
    search_fields = ('title', 'user__username')  # Ajout de la recherche par titre et utilisateur
    actions = ['activate_ads', 'deactivate_ads']  # Actions personnalisées

    def activate_ads(self, request, queryset):
        queryset.update(active=True)
        self.message_user(request, "Selected ads have been activated.")
    
    def deactivate_ads(self, request, queryset):
        queryset.update(active=False)
        self.message_user(request, "Selected ads have been deactivated.")
    
    activate_ads.short_description = "Activate selected ads"
    deactivate_ads.short_description = "Deactivate selected ads"

admin.site.register(Ad, AdAdmin)
