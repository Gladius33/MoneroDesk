from django.contrib import admin
from .models import Profile

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'xmr_balance', 'referral_code', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at', 'xmr_balance')  # Filters for easier navigation
    search_fields = ('user__username', 'referral_code')  # Search by username or referral code
    readonly_fields = ('xmr_balance', 'user_subaddress', 'created_at', 'updated_at')  # Fields not editable

    # Editable fields in list view
    list_editable = ('referral_code',)  

    # Custom actions for bulk operations
    actions = ['reset_referral_code', 'update_xmr_balance']

    # Organizing fields into sections with fieldsets
    fieldsets = (
        (None, {
            'fields': ('user', 'profile_picture', 'bio')
        }),
        ('Monero Information', {
            'fields': ('user_subaddress', 'xmr_balance'),
            'classes': ('collapse',)
        }),
        ('Referral Details', {
            'fields': ('referral_code', 'referred_users'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Custom action to reset referral codes
    def reset_referral_code(self, request, queryset):
        queryset.update(referral_code=None)
        self.message_user(request, "Referral codes reset successfully.")

    reset_referral_code.short_description = "Reset referral code for selected profiles"

    # Custom action to update XMR balances
    def update_xmr_balance(self, request, queryset):
        for profile in queryset:
            profile.update_balance_and_transactions()
        self.message_user(request, "XMR balances updated successfully.")

    update_xmr_balance.short_description = "Update XMR balance for selected profiles"

    # Limiting the number of profiles displayed per page
    list_per_page = 25

# Register the updated ProfileAdmin class
admin.site.register(Profile, ProfileAdmin)
