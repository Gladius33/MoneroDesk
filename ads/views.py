from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Ad
from .forms import AdForm
from django.contrib import messages
from decimal import Decimal
from transactions.models import Transaction
from monero_app.models import MoneroRate

@login_required
def ad_list_view(request):
    """
    View to display the list of ads.
    Allows filtering ads by type (buy or sell) and cryptocurrency.
    """
    ads = Ad.objects.filter(active=True)  # Only show active ads

    # Filtering ads by type and cryptocurrency
    ad_type = request.GET.get('type', '')
    crypto_currency = request.GET.get('crypto_currency', '')

    if ad_type:
        ads = ads.filter(type=ad_type)
    if crypto_currency:
        ads = ads.filter(crypto_currency=crypto_currency)

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


@login_required
def ad_detail_view(request, ad_id):
    """
    View to display the details of an ad.
    Allows creating a transaction by clicking 'Buy Now' or 'Sell Now'.
    """
    ad = get_object_or_404(Ad, id=ad_id)

    if request.method == 'POST':
        # Handle transaction creation
        try:
            transaction_amount = Decimal(request.POST.get('transaction_amount'))
            if transaction_amount < ad.min_amount or transaction_amount > ad.max_amount:
                raise ValueError("The amount does not meet the ad's limits.")

            # Check if dynamic price is enabled, and update the price dynamically if necessary
            if ad.dynamic_price:
                monero_rate = MoneroRate.objects.get(currency=ad.fiat_currency)
                adjustment = monero_rate.rate * (ad.dynamic_price_value / 100)
                ad.price = monero_rate.rate + adjustment
                ad.save()

            if ad.type == 'sell':
                # The user is buying XMR
                Transaction.objects.create_sell_transaction(
                    buyer=request.user,
                    ad=ad,
                    transaction_amount=transaction_amount
                )
                messages.success(request, "Your purchase transaction has been created.")
            elif ad.type == 'buy':
                # The user is selling XMR
                Transaction.objects.create_buy_transaction(
                    seller=request.user,
                    ad=ad,
                    transaction_amount=transaction_amount
                )
                messages.success(request, "Your sale transaction has been created.")
                
            return redirect('ad_list')

        except ValueError as e:
            messages.error(request, str(e))
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