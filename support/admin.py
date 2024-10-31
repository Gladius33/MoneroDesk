from django.contrib import admin
from .models import SupportRequest, ChatArchive

class SupportRequestAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'status', 'support_agent', 'created_at', 'closed_at']
    list_filter = ['status', 'support_agent', 'created_at', 'closed_at']  # Allows filtering by these fields
    search_fields = ['transaction__id', 'support_agent__username']  # Add search by transaction ID and agent username
    readonly_fields = ['created_at', 'closed_at']  # Make these fields read-only

    def has_add_permission(self, request):
        # Disable adding support requests manually via admin
        return False

    def has_delete_permission(self, request, obj=None):
        # Disable deleting support requests manually via admin
        return False

class ChatArchiveAdmin(admin.ModelAdmin):
    list_display = ['support_request', 'archived_at']
    readonly_fields = ['archived_at', 'chat_data']  # Prevent editing archived data
    search_fields = ['support_request__transaction__id']

admin.site.register(SupportRequest, SupportRequestAdmin)
admin.site.register(ChatArchive, ChatArchiveAdmin)
