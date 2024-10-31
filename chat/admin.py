from django.contrib import admin
from .models import Message, ChatEncryptionKey

class MessageAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'sender', 'created_at', 'file', 'encrypted')
    list_filter = ('transaction', 'sender', 'created_at', 'encrypted')  # Added encrypted filter
    search_fields = ('sender__username', 'transaction__id')  # Search for users and transactions
    readonly_fields = ('encrypted', 'created_at')  # Avoid unwanted modification
    
    # Link transaction to its detail page
    def transaction(self, obj):
        return f"<a href='/admin/transactions/transaction/{obj.transaction.id}/'>{obj.transaction.id}</a>"
    transaction.allow_tags = True
    transaction.short_description = "Transaction Link"

    # Custom action to delete encrypted messages
    def delete_encrypted_messages(self, request, queryset):
        count = queryset.filter(encrypted=True).delete()[0]
        self.message_user(request, f"Deleted {count} encrypted messages.")

    delete_encrypted_messages.short_description = "Delete Encrypted Messages"
    actions = ['delete_encrypted_messages']

class ChatEncryptionKeyAdmin(admin.ModelAdmin):
    list_display = ('transaction',)
    search_fields = ('transaction__id',)

admin.site.register(Message, MessageAdmin)
admin.site.register(ChatEncryptionKey, ChatEncryptionKeyAdmin)
