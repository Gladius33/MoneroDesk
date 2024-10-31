from django.contrib import admin
from .models import XmrWallet, XmrSubaddress, MoneroTransaction, MoneroRate

@admin.register(XmrWallet)
class XmrWalletAdmin(admin.ModelAdmin):
    list_display = ('address', 'balance', 'wallet_type')
    search_fields = ('address',)
    list_filter = ('wallet_type', 'balance')

@admin.register(XmrSubaddress)
class XmrSubaddressAdmin(admin.ModelAdmin):
    list_display = ('address', 'wallet_type', 'user')
    search_fields = ('address', 'user__username')
    list_filter = ('wallet_type',)

@admin.register(MoneroTransaction)
class MoneroTransactionAdmin(admin.ModelAdmin):
    list_display = ('tx_hash', 'amount', 'status', 'confirmations', 'created_at')
    list_filter = ('status', 'confirmations')
    search_fields = ('tx_hash', 'status')

@admin.register(MoneroRate)
class MoneroRateAdmin(admin.ModelAdmin):
    list_display = ('currency', 'rate', 'inverse_rate', 'last_updated')
    search_fields = ('currency',)
    list_filter = ('last_updated',)
