from django.contrib import admin
from .models import Transaction, AutoRefundUserList
from django.contrib.auth.models import User
from decimal import Decimal
from monero_app.services import MoneroService

class AutoRefundUserListAdmin(admin.ModelAdmin):
    list_display = ('user', 'auto_refund_enabled')
    search_fields = ('user__username',)
    list_filter = ('auto_refund_enabled',)

    actions = ['enable_auto_refund', 'disable_auto_refund']

    def enable_auto_refund(self, request, queryset):
        queryset.update(auto_refund_enabled=True)
        self.message_user(request, "Auto refund enabled for selected users.")

    def disable_auto_refund(self, request, queryset):
        queryset.update(auto_refund_enabled=False)
        self.message_user(request, "Auto refund disabled for selected users.")

    enable_auto_refund.short_description = "Enable auto refund for selected users"
    disable_auto_refund.short_description = "Disable auto refund for selected users"


class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_id', 'buyer', 'seller', 'transaction_amount', 'fee_percentage', 
        'fiat_currency', 'status', 'created_at', 'get_crypto_type'
    )
    list_filter = ('status', 'fiat_currency', 'created_at', 'ad__type')  # Filter by transaction status, currency, etc.
    search_fields = ('transaction_id', 'buyer__username', 'seller__username', 'ad__title')
    readonly_fields = ('transaction_id', 'created_at')  # Fields that shouldn't be modified in the admin

    actions = ['refund_fees', 'enable_auto_refund', 'disable_auto_refund']

    def get_crypto_type(self, obj):
        """
        Affiche le type de crypto utilisé dans la transaction.
        """
        return obj.ad.crypto_currency
    get_crypto_type.short_description = 'Crypto Type'

    def refund_fees(self, request, queryset):
        """
        Action pour rembourser manuellement les frais d'une ou plusieurs transactions.
        """
        total_refund = Decimal('0.00')
        monero_service = MoneroService()

        for transaction in queryset.filter(status='completed'):
            fee_amount = transaction.transaction_amount * transaction.fee_percentage / 100
            total_refund += fee_amount

            # Remboursement effectif via MoneroService
            monero_service.send_xmr(to_address=transaction.buyer.profile.user_subaddress, amount=fee_amount)

        self.message_user(request, f"Total refund of {total_refund} XMR processed for selected transactions.")

    refund_fees.short_description = "Refund fees for selected transactions"

    def enable_auto_refund(self, request, queryset):
        """
        Activer le remboursement automatique pour les utilisateurs sélectionnés.
        """
        for transaction in queryset:
            AutoRefundUserList.objects.update_or_create(user=transaction.buyer, defaults={'auto_refund_enabled': True})
        self.message_user(request, "Auto refund enabled for selected users.")

    enable_auto_refund.short_description = "Enable auto refund for selected users"

    def disable_auto_refund(self, request, queryset):
        """
        Désactiver le remboursement automatique pour les utilisateurs sélectionnés.
        """
        for transaction in queryset:
            AutoRefundUserList.objects.update_or_create(user=transaction.buyer, defaults={'auto_refund_enabled': False})
        self.message_user(request, "Auto refund disabled for selected users.")

    disable_auto_refund.short_description = "Disable auto refund for selected users"


# Enregistrement des modèles dans l'admin
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(AutoRefundUserList, AutoRefundUserListAdmin)
