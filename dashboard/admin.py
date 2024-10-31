from django.contrib import admin
from .models import AdminSettings

class AdminSettingsAdmin(admin.ModelAdmin):
    """
    This class customizes the admin interface for AdminSettings model.
    """
    list_display = ('fee_percentage', 'withdraw_fee_percentage', 'xmr_wallet_address', 'referral_percentage')
    search_fields = ('xmr_wallet_address', 'fee_percentage', 'withdraw_fee_percentage')
    list_filter = ('fee_percentage', 'withdraw_fee_percentage')  # Filters for admin filtering options
    readonly_fields = ('referral_percentage',)  # Makes this field read-only
    fieldsets = (
        ('General Settings', {
            'fields': ('fee_percentage', 'withdraw_fee_percentage', 'xmr_wallet_address'),
            'description': 'Manage the general settings for fees and wallet address.',
        }),
        ('Referral Settings', {
            'fields': ('referral_percentage',),
            'description': 'Manage the referral program settings.',
        }),
    )
    ordering = ('fee_percentage',)  # Orders the records by fee_percentage in the admin interface

    def has_delete_permission(self, request, obj=None):
        """
        Prevents deletion of AdminSettings in the admin panel.
        """
        return False

    def has_add_permission(self, request):
        """
        Limits the admin interface to allow only editing the single AdminSettings record.
        """
        return False if AdminSettings.objects.exists() else True

admin.site.register(AdminSettings, AdminSettingsAdmin)
