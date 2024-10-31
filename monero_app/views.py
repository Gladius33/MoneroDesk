from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .services import MoneroService
from .models import XmrSubaddress, MoneroRate
from decimal import Decimal
from django.conf import settings
from django.contrib.auth.decorators import login_required

monero_service = MoneroService()

@login_required
def create_user_subaddress_view(request):
    """
    Vue pour créer une sous-adresse pour un utilisateur.
    """
    label = f"User {request.user.username}"
    subaddress = monero_service.create_user_subaddress(label=label)
    
    if subaddress:
        XmrSubaddress.objects.create(
            address=subaddress,
            wallet_type='user',
            label=label,
            user=request.user
        )
        return JsonResponse({'status': 'success', 'subaddress': subaddress})
    else:
        return JsonResponse({'status': 'error', 'message': 'Failed to create subaddress'})

@login_required
def create_fee_subaddress_view(request):
    """
    Vue pour créer une sous-adresse dédiée aux frais.
    """
    label = 'Fee Wallet'
    subaddress = monero_service.create_fee_subaddress(label=label)
    
    if subaddress:
        XmrSubaddress.objects.create(
            address=subaddress,
            wallet_type='fee',
            label=label
        )
        return JsonResponse({'status': 'success', 'subaddress': subaddress})
    else:
        return JsonResponse({'status': 'error', 'message': 'Failed to create fee subaddress'})

@login_required
def create_escrow_subaddress_view(request):
    """
    Vue pour créer une sous-adresse dédiée au séquestre.
    """
    label = 'Escrow Wallet'
    subaddress = monero_service.create_escrow_subaddress(label=label)
    
    if subaddress:
        XmrSubaddress.objects.create(
            address=subaddress,
            wallet_type='escrow',
            label=label
        )
        return JsonResponse({'status': 'success', 'subaddress': subaddress})
    else:
        return JsonResponse({'status': 'error', 'message': 'Failed to create escrow subaddress'})

@login_required
def subaddress_balance_view(request, subaddress_index):
    """
    Vue pour obtenir le solde et les transactions d'une sous-adresse.
    """
    balance_data = monero_service.get_subaddress_balance_and_transactions(subaddress_index=subaddress_index)
    
    if balance_data:
        return JsonResponse({
            'status': 'success',
            'balance': balance_data['balance'],
            'unlocked_balance': balance_data['unlocked_balance'],
            'transactions': balance_data['transactions']
        })
    else:
        return JsonResponse({'status': 'error', 'message': 'Failed to fetch balance and transactions'})

@csrf_exempt
def send_xmr_view(request):
    """
    Vue pour envoyer des XMR à une adresse donnée.
    """
    if request.method == 'POST':
        to_address = request.POST.get('to_address')
        amount = Decimal(request.POST.get('amount'))
        internal = request.POST.get('internal', False) == 'true'
        fee = request.POST.get('fee', False) == 'true'
        escrow = request.POST.get('escrow', False) == 'true'
        
        tx_hash = monero_service.send_xmr(to_address, amount, internal=internal, fee=fee, escrow=escrow)
        
        if tx_hash:
            return JsonResponse({'status': 'success', 'tx_hash': tx_hash})
        else:
            return JsonResponse({'status': 'error', 'message': 'Transaction failed'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def fetch_rates_view(request):
    """
    Vue pour récupérer et mettre à jour les taux de change du Monero en différentes devises.
    """
    try:
        monero_service.fetch_rates()
        rates = MoneroRate.objects.all()
        rates_data = {rate.currency: {'rate': rate.rate, 'inverse_rate': rate.inverse_rate} for rate in rates}
        return JsonResponse({'status': 'success', 'rates': rates_data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

