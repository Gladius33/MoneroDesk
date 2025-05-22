from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Ad
from .forms import AdForm
from django.contrib import messages
from decimal import Decimal, InvalidOperation
from transactions.models import Transaction
from monero_app.models import MoneroRate
from django.db.models import Q

def home_view(request):
    return ad_list_view(request)

@login_required
def ad_list_view(request):
    """
    View to display the list of ads with filtering capabilities
    """
    ads = Ad.objects.filter(active=True)  # Only show active ads

    # Get filtering parameters from GET request
    query = request.GET.get('query', '')
    ad_type = request.GET.get('type', '')
    crypto_currency = request.GET.get('crypto_currency', '')
    fiat_currency = request.GET.get('fiat_currency', '')
    payment_method = request.GET.get('payment_method', '')
    min_price = request.GET.get('min_price', None)
    max_price = request.GET.get('max_price', None)
    user = request.GET.get('user', '')

    # Apply filters based on the user input
    if query:
        ads = ads.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if ad_type:
        ads = ads.filter(type=ad_type)
    if crypto_currency:
        ads = ads.filter(crypto_currency=crypto_currency)
    if fiat_currency:
        ads = ads.filter(fiat_currency__icontains=fiat_currency)
    if payment_method:
        ads = ads.filter(payment_method__icontains=payment_method)
    if min_price:
        ads = ads.filter(price__gte=Decimal(min_price))
    if max_price:
        ads = ads.filter(price__lte=Decimal(max_price))
    if user:
        ads = ads.filter(user__username__icontains=user)

    return render(request, 'ads/ad_list.html', {'ads': ads})

@login_required
def ad_create_view(request):
    """
    View to create a new ad.
    For sell ads, creates an escrow wallet.
    """
    if request.method == 'POST':
        form = AdForm(request.POST)
        if form.is_valid():
            ad = form.save(commit=False)
            ad.user = request.user

            # Check if dynamic price is enabled
            if ad.dynamic_price:
                # Get the latest XMR to fiat rate
                monero_rate = MoneroRate.objects.get(currency=ad.fiat_currency)
                adjustment = monero_rate.rate * (ad.dynamic_price_value / 100)
                ad.price = monero_rate.rate + adjustment  # Update the ad price
                messages.info(request, "The price has been dynamically set according to the market rate.")

            ad.save()

            if ad.type == 'sell':
                ad.create_escrow_wallet()
                messages.success(request, "Your escrow wallet has been created for this ad.")

            return redirect('ad_list')
    else:
        form = AdForm()
    return render(request, 'ads/ad_form.html', {'form': form})

def normalize_amount(amount_str):
    """Formate à 8 décimales, accepte virgule ou point, complète avec des zéros."""
    if not amount_str:
        return None
    amount_str = amount_str.replace(',', '.').strip()
    if '.' in amount_str:
        integer, decimals = amount_str.split('.', 1)
        decimals = (decimals + '0'*8)[:8]
    else:
        integer = amount_str
        decimals = '0'*8
    return f"{integer}.{decimals}"

@login_required
def ad_detail_view(request, ad_id):
    """
    View to display the details of an ad.
    Allows creating a transaction by clicking 'Buy Now' or 'Sell Now'.
    """
    ad = get_object_or_404(Ad, id=ad_id)

    if request.method == 'POST':
        user_input = request.POST.get('amount')
        if not user_input:
            messages.error(request, "Vous devez indiquer un montant.")
            return redirect('ad_detail', ad_id=ad.id)
        try:
            formatted_amount = normalize_amount(user_input)
            transaction_amount = Decimal(formatted_amount)

            if transaction_amount < ad.min_amount or transaction_amount > ad.max_amount:
                raise ValueError("The amount does not meet the ad's limits.")

            if ad.dynamic_price:
                monero_rate = MoneroRate.objects.get(currency=ad.fiat_currency)
                adjustment = monero_rate.rate * (ad.dynamic_price_value / 100)
                ad.price = monero_rate.rate + adjustment
                ad.save()

            if ad.type == 'sell':
                Transaction.objects.create_sell_transaction(
                    buyer=request.user,
                    ad=ad,
                    transaction_amount=transaction_amount
                )
                messages.success(request, "Your purchase transaction has been created.")
            elif ad.type == 'buy':
                Transaction.objects.create_buy_transaction(
                    seller=request.user,
                    ad=ad,
                    transaction_amount=transaction_amount
                )
                messages.success(request, "Your sale transaction has been created.")

            return redirect('ad_list')
        except (InvalidOperation, ValueError) as e:
            messages.error(request, f"Erreur : {str(e)}")
            return redirect('ad_detail', ad_id=ad.id)

    return render(request, 'ads/ad_detail.html', {'ad': ad})

@login_required
def ad_delete_view(request, ad_id):
    """
    View to delete an ad.
    Ensures there are no pending transactions before deletion.
    """
    ad = get_object_or_404(Ad, id=ad_id)
    if ad.user != request.user:
        messages.error(request, "You do not have permission to delete this ad.")
        return redirect('ad_detail', ad_id=ad.id)

    # Check for active transactions
    active_transactions = ad.transaction_set.filter(status='pending').count()
    if active_transactions > 0:
        messages.error(request, "You cannot delete this ad while transactions are pending.")
        return redirect('ad_detail', ad_id=ad.id)

    # Release escrow funds if applicable
    ad.release_escrow_on_deletion()
    ad.delete()
    messages.success(request, "The ad has been deleted and funds have been released.")
    return redirect('ad_list')

