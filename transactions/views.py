from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from chat.models import ChatEncryptionKey
from chat.views import decrypt_messages, encrypt_message, encrypt_file, Message
from monero_app.services import MoneroService
from .models import Transaction
from .forms import BuyTransactionForm
from datetime import timedelta
from django.utils import timezone
from ads.models import Ad


@login_required
def transaction_detail_view(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    profile = request.user.profile
    chosen_fiat = profile.selected_fiat_currency
    def some_view(request):
    monero_service = MoneroService()

    # Fetch XMR to fiat rate and calculate price
    xmr_to_fiat_rate = monero_service.get_monero_rate(chosen_fiat)
    fiat_price = transaction.transaction_amount * xmr_to_fiat_rate

    # Fetch chat encryption key and decrypt the messages
    chat_key = get_object_or_404(ChatEncryptionKey, transaction=transaction)
    decrypted_messages = decrypt_messages(transaction.messages.all(), chat_key, request.user)

    # Handle the chat message POST
    if request.method == 'POST':
        text = request.POST.get('text')
        file = request.FILES.get('file')
        encrypted_text = encrypt_message(text, chat_key, request.user) if text else None
        encrypted_file = encrypt_file(file, chat_key, request.user) if file else None

        if text or file:
            Message.objects.create(
                transaction=transaction,
                sender=request.user,
                text=encrypted_text,
                file=encrypted_file
            )

    # Manage transaction type (sell/buy)
    if transaction.ad.type == 'sell':
        payment_button_visible = not transaction.payment_sent
        escrow_address = transaction.ad.escrow_wallet_address
        show_escrow_qr = False
        disable_cancel_button = (timezone.now() - transaction.created_at) > timedelta(hours=1, minutes=30) and not transaction.payment_sent
    else:
        escrow_info = monero_service.create_escrow_subaddress(label=f"Escrow_Transaction_{transaction.id}")
        escrow_address = escrow_info['address']
        show_escrow_qr = True

        # Check seller's balance
        seller_balance = monero_service.get_balance(transaction.seller.profile.user_subaddress)
        if seller_balance >= transaction.transaction_amount:
            monero_service.send_xmr(to_address=escrow_address, amount=transaction.transaction_amount, escrow=True)
            show_escrow_qr = False
        else:
            remaining_amount = transaction.transaction_amount - seller_balance
            messages.info(request, f"Please send {remaining_amount} XMR to the escrow.")
        
        confirmations = monero_service.get_confirmations(escrow_address)
        disable_cancel_button = confirmations >= 5 and transaction.payment_sent

    return render(request, 'transactions/transaction_detail.html', {
        'transaction': transaction,
        'chat': decrypted_messages,
        'fiat_price': fiat_price,
        'chosen_fiat': chosen_fiat,
        'xmr_amount': transaction.transaction_amount,
        'escrow_address': escrow_address,
        'show_escrow_qr': show_escrow_qr,
        'payment_button_visible': payment_button_visible,
        'confirmations': confirmations if 'confirmations' in locals() else None,
        'disable_cancel_button': disable_cancel_button
    })


@login_required
def transaction_list_view(request):
    """
    Displays a list of transactions for the logged-in user.
    """
    transactions = Transaction.objects.filter(buyer=request.user) | Transaction.objects.filter(seller=request.user)
    return render(request, 'transactions/transaction_list.html', {'transactions': transactions})


@login_required
def cancel_transaction_view(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    if (timezone.now() - transaction.created_at) > timedelta(hours=1, minutes=30) and transaction.payment_sent:
        messages.error(request, "You cannot cancel the transaction after the payment has been sent.")
        return redirect('transaction_detail', transaction_id=transaction.id)

    # Handle cancellation logic based on type
    transaction.cancel_transaction()

    if transaction.ad.type == 'sell':
        monero_service = MoneroService()
        # Refund escrow to seller's wallet
        monero_service.return_funds_to_user(transaction.ad.escrow_wallet_address, transaction.transaction_amount)
    elif transaction.ad.type == 'buy':
        monero_service = MoneroService()
        if monero_service.check_escrow_balance(transaction.escrow_wallet_address) > 0:
            monero_service.return_funds_to_user(transaction.escrow_wallet_address, transaction.transaction_amount)

    messages.success(request, 'Transaction has been canceled.')
    return redirect('transaction_detail', transaction_id=transaction.id)


@login_required
def release_funds_view(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    monero_service = MoneroService()

    if transaction.ad.type == 'sell':
        monero_service.release_funds(transaction.ad.escrow_wallet_address, transaction.buyer.profile.user_subaddress)
    elif transaction.ad.type == 'buy':
        monero_service.release_funds(transaction.escrow_wallet_address, transaction.buyer.profile.user_subaddress)

    messages.success(request, 'Funds have been released to the buyer.')
    return redirect('transaction_detail', transaction_id=transaction.id)


@login_required
def payment_sent_view(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    # Mark payment as sent
    transaction.payment_sent = True
    transaction.save()

    messages.success(request, 'Payment marked as sent.')
    return redirect('transaction_detail', transaction_id=transaction.id)


@login_required
def create_buy_transaction_view(request, ad_id):
    ad = get_object_or_404(Ad, id=ad_id)
    
    if ad.type != 'buy':
        messages.error(request, "This is not a valid buy transaction.")
        return redirect('ad_detail', ad_id=ad.id)
    
    if request.method == 'POST':
        form = BuyTransactionForm(request.POST, ad=ad)
        if form.is_valid():
            transaction_amount = form.cleaned_data['transaction_amount']
            transaction = Transaction.create_buy_transaction(seller=request.user, ad=ad, transaction_amount=transaction_amount)
            messages.success(request, 'Transaction created successfully.')
            return redirect('transaction_detail', transaction_id=transaction.id)
    else:
        form = BuyTransactionForm(ad=ad)

    return render(request, 'transactions/create_buy_transaction.html', {
        'form': form,
        'ad': ad
    })
