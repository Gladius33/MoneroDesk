from django.contrib import admin
from .models import Message, ChatEncryptionKey

class MessageAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'sender', 'created_at', 'file', 'encrypted')
    list_filter = ('transaction', 'sender', 'created_at')  # Ajout de filtres pour mieux naviguer
    search_fields = ('sender__username', 'transaction__id')  # Ajout de la recherche par utilisateur et transaction
    readonly_fields = ('encrypted', 'created_at')  # Pour éviter toute modification non voulue

class ChatEncryptionKeyAdmin(admin.ModelAdmin):
    list_display = ('transaction',)
    search_fields = ('transaction__id',)

admin.site.register(Message, MessageAdmin)
admin.site.register(ChatEncryptionKey, ChatEncryptionKeyAdmin)

