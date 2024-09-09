from django.contrib import admin
from .models import SupportRequest, ChatArchive

class SupportRequestAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'status', 'support_agent', 'created_at', 'closed_at']

admin.site.register(SupportRequest, SupportRequestAdmin)
admin.site.register(ChatArchive)
