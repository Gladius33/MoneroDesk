import os
import requests
from django.conf import settings
from monero.wallet import Wallet
from monero.backends.jsonrpc import JSONRPCWallet
from .models import MoneroRate
import logging

logger = logging.getLogger(__name__)

class MoneroService:
    def __init__(self):
        self.rpc_wallet_url = f"http://{settings.XMR_RPC_HOST}:{settings.XMR_RPC_PORT}/json_rpc"
        self.wallet_rpc = JSONRPCWallet(self.rpc_wallet_url)
        self.wallet_directory = os.path.join(settings.BASE_DIR, 'XMR_WALLET')
        self.main_wallet_name = "XMR_WALLET"  # Main wallet name on the system

    def check_or_create_main_wallet(self):
        wallet_file = os.path.join(self.wallet_directory, f"{self.main_wallet_name}.keys")
        if not os.path.exists(wallet_file):
            wallet_pass = settings.WALLET_PASS
            os.makedirs(self.wallet_directory, exist_ok=True)

            try:
                self.wallet_rpc.create_wallet(
                    wallet_name=self.main_wallet_name,
                    password=wallet_pass,
                    language='English'
                )
                logger.info("Main Monero wallet created successfully.")
            except Exception as e:
                logger.error(f"Error creating main wallet: {e}")
        else:
            logger.info("Main Monero wallet already exists.")
        
        self.wallet_rpc.open_wallet(wallet_name=self.main_wallet_name, password=settings.WALLET_PASS)

    def create_user_subaddress(self, label=None):
        wallet_pass = settings.WALLET_PASS
        try:
            self.wallet_rpc.open_wallet(wallet_name=self.main_wallet_name, password=wallet_pass)
        except Exception as e:
            logger.error(f"Error opening main wallet: {e}")
            return None

        try:
            subaddress = self.wallet_rpc.create_address(account_index=0, label=label)
            logger.info(f"Monero subaddress created: {subaddress}")
            return subaddress
        except Exception as e:
            logger.error(f"Error creating subaddress: {e}")
            return None

    def create_fee_subaddress(self, label=None):
        wallet_pass = settings.WALLET_PASS
        try:
            self.wallet_rpc.open_wallet(wallet_name=self.main_wallet_name, password=wallet_pass)
        except Exception as e:
            logger.error(f"Error opening the main wallet: {e}")
            return None
        try:
            subaddress = self.wallet_rpc.create_address(account_index=1, label=label)
            logger.info(f"Monero fee subaddress created: {subaddress}")
            return subaddress
        except Exception as e:
            logger.error(f"Error creating the fee subaddress: {e}")
            return None

    def create_escrow_subaddress(self, label=None):
        wallet_pass = settings.WALLET_PASS
        try:
            self.wallet_rpc.open_wallet(wallet_name=self.main_wallet_name, password=wallet_pass)
        except Exception as e:
            logger.error(f"Error opening the main wallet: {e}")
            return None

        try:
            subaddress = self.wallet_rpc.create_address(account_index=2, label=label)
            logger.info(f"Monero escrow subaddress created: {subaddress}")
            return subaddress
        except Exception as e:
            logger.error(f"Error creating the escrow subaddress: {e}")
            return None

    def get_subaddress_balance_and_transactions(self, subaddress_index):
        try:
            self.wallet_rpc.open_wallet(wallet_name=self.main_wallet_name, password=settings.WALLET_PASS)
            balance_info = self.wallet_rpc.get_balance(account_index=0, address_index=subaddress_index)
            balance = balance_info['balance'] / 1e12
            unlocked_balance = balance_info['unlocked_balance'] / 1e12

            incoming_transfers = self.wallet_rpc.incoming_transfers(account_index=0, address_indices=[subaddress_index])
            transactions = []
            for transfer in incoming_transfers:
                transactions.append({
                    'amount': transfer['amount'] / 1e12,
                    'txid': transfer['txid'],
                    'confirmations': transfer['confirmations'],
                    'status': 'unconfirmed' if transfer['confirmations'] < 5 else 'confirmed'
                })

            return {
                'balance': balance,
                'unlocked_balance': unlocked_balance,
                'transactions': transactions
            }
        except Exception as e:
            logger.error(f"Error fetching balance and transactions: {e}")
            return None

    def send_xmr(self, to_address, amount, internal=False, fee=False, escrow=False):
        try:
            self.wallet_rpc.open_wallet(wallet_name=self.main_wallet_name, password=settings.WALLET_PASS)
            amount_atomic = int(amount * 1e12)
            priority = 2

            destinations = [{'address': to_address, 'amount': amount_atomic}]
            if internal:
                if fee:
                    logger.info("Sending to fee subaddress")
                elif escrow:
                    logger.info("Sending to escrow subaddress")
            else:
                tx_hash = self.wallet_rpc.transfer(destinations=destinations, priority=priority)
                logger.info(f"Transaction sent. TX Hash: {tx_hash}")
                return tx_hash
        except Exception as e:
            logger.error(f"Error sending transaction: {e}")
            return None

    def fetch_rates(self):
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
        headers = {'X-CMC_PRO_API_KEY': settings.X_CMC_PRO_API_KEY}
        params = {'symbol': 'XMR', 'convert': 'USD,BTC,EUR,CHF,RUB,CAD,CNY'}
        response = requests.get(url, headers=headers, params=params)
        rates = response.json()['data']['XMR']['quote']

        for currency, data in rates.items():
            MoneroRate.objects.update_or_create(
                currency=currency,
                defaults={
                    'rate': data['price'],
                    'inverse_rate': 1 / data['price']
                }
            )
