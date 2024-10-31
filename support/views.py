from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from .models import SupportRequest, ChatArchive
from transactions.models import Transaction
from django.utils import timezone
from monero_app.services import MoneroService  # Import for handling Monero-related functionality
from django.contrib import messages

def is_support_agent(user):
    return user.groups.filter(name='Support').exists()

@user_passes_test(is_support_agent)
def support_dashboard(request):
    support_requests = SupportRequest.objects.filter(status='waiting')
    return render(request, 'support/support_dashboard.html', {'support_requests': support_requests})

@user_passes_test(is_support_agent)
def join_chat(request, support_id):
    support_request = get_object_or_404(SupportRequest, id=support_id)
    support_request.support_agent = request.user
    support_request.status = 'in_room'
    support_request.save()
    return JsonResponse({'status': 'joined', 'chat_url': f"/transactions/{support_request.transaction.id}/"})

@user_passes_test(is_support_agent)
def leave_chat(request, support_id):
    support_request = get_object_or_404(SupportRequest, id=support_id)
    support_request.status = 'closed'
    support_request.closed_at = timezone.now()
    support_request.save()
    return JsonResponse({'status': 'left'})

@user_passes_test(is_support_agent)
def archive_chat(request, support_id):
    support_request = get_object_or_404(SupportRequest, id=support_id)
    chat = support_request.transaction.messages.all()  # Assuming you have messages stored in the transaction
    chat_data = '\n'.join([f"{msg.sender}: {msg.text}" for msg in chat])
    ChatArchive.objects.create(support_request=support_request, chat_data=chat_data)
    return JsonResponse({'status': 'archived'})

@user_passes_test(is_support_agent)
def cancel_transaction(request, support_id):
    """
    Allows a support agent to cancel a transaction and refund the seller.
    """
    support_request = get_object_or_404(SupportRequest, id=support_id)
    transaction = support_request.transaction
    monero_service = MoneroService()

    if transaction.ad.type == 'sell':
        # Refund the escrow to the seller
        monero_service.return_funds_to_user(transaction.ad.escrow_wallet_address, transaction.transaction_amount)
        transaction.status = 'canceled'
        transaction.save()
        support_request.status = 'closed'
        support_request.closed_at = timezone.now()
        support_request.action_taken = 'canceled'
        support_request.save()

    messages.success(request, 'Transaction canceled and escrow funds refunded to the seller.')
    return redirect('support_dashboard')

@user_passes_test(is_support_agent)
def validate_transaction(request, support_id):
    """
    Allows a support agent to validate the transaction and release escrow funds to the buyer.
    """
    support_request = get_object_or_404(SupportRequest, id=support_id)
    transaction = support_request.transaction
    monero_service = MoneroService()

    if transaction.ad.type == 'sell':
        # Release the escrow funds to the buyer
        monero_service.release_funds(transaction.ad.escrow_wallet_address, transaction.buyer.profile.user_subaddress)
        transaction.status = 'completed'
        transaction.save()

    support_request.status = 'closed'
    support_request.closed_at = timezone.now()
    support_request.action_taken = 'validated'
    support_request.save()

    messages.success(request, 'Transaction validated and escrow funds released to the buyer.')
    return redirect('support_dashboard')
