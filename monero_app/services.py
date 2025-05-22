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
        # Initialisation du backend JSONRPCWallet
        self.wallet_backend = JSONRPCWallet(
            host=settings.XMR_RPC_HOST,
            port=settings.XMR_RPC_PORT,
            user=getattr(settings, "XMR_RPC_USER", None),
            password=getattr(settings, "XMR_RPC_PASSWORD", None)
        )
        # L'objet Wallet monero-python
        self.wallet = Wallet(self.wallet_backend)
        self.wallet_directory = os.path.join(settings.BASE_DIR, 'XMR_WALLET')
        self.main_wallet_name = "XMR_WALLET"

    def check_or_create_main_wallet(self):
        wallet_file = os.path.join(self.wallet_directory, f"{self.main_wallet_name}.keys")
        if not os.path.exists(wallet_file):
            logger.warning("Main wallet file does not exist! You must create it manually via RPC or CLI before usage.")
            # Pour créer le wallet via API JSON-RPC direct, exemple (hors monero-python) :
            '''
            import json
            import requests
            url = f"http://{settings.XMR_RPC_HOST}:{settings.XMR_RPC_PORT}/json_rpc"
            data = {
                "jsonrpc":"2.0",
                "id":"0",
                "method":"create_wallet",
                "params":{
                    "filename": self.main_wallet_name,
                    "password": settings.WALLET_PASS,
                    "language": "English"
                }
            }
            resp = requests.post(url, json=data)
            logger.info(f"Wallet creation response: {resp.text}")
            '''
        else:
            logger.info("Main Monero wallet already exists.")

    def create_user_subaddress(self, label=None):
        try:
            account = self.wallet.accounts[0]  # Compte principal
            subaddress = account.new_subaddress(label=label)
            logger.info(f"Monero subaddress created: {subaddress.address}")
            return subaddress.address
        except Exception as e:
            logger.error(f"Error creating subaddress: {e}")
            return None

    def create_fee_subaddress(self, label=None):
        try:
            # On utilise ici le deuxième compte (index 1)
            account = self.wallet.accounts[1]
            subaddress = account.new_subaddress(label=label)
            logger.info(f"Monero fee subaddress created: {subaddress.address}")
            return subaddress.address
        except Exception as e:
            logger.error(f"Error creating the fee subaddress: {e}")
            return None

    def create_escrow_subaddress(self, label=None):
        try:
            # Troisième compte (index 2)
            account = self.wallet.accounts[2]
            subaddress = account.new_subaddress(label=label)
            logger.info(f"Monero escrow subaddress created: {subaddress.address}")
            return subaddress.address
        except Exception as e:
            logger.error(f"Error creating the escrow subaddress: {e}")
            return None

    def get_subaddress_balance_and_transactions(self, subaddress_index, account_index=0):
        try:
            account = self.wallet.accounts[account_index]
            subaddress = account.subaddresses[subaddress_index]
            balance = subaddress.balance
            unlocked_balance = subaddress.unlocked_balance

            transactions = []
            for tx in subaddress.incoming():
                transactions.append({
                    'amount': float(tx.amount),
                    'txid': tx.hash,
                    'confirmations': tx.confirmations,
                    'status': 'unconfirmed' if tx.confirmations < 5 else 'confirmed'
                })
            return {
                'balance': float(balance),
                'unlocked_balance': float(unlocked_balance),
                'transactions': transactions
            }
        except Exception as e:
            logger.error(f"Error fetching balance and transactions: {e}")
            return None

    def send_xmr(self, to_address, amount, account_index=0, subaddr_indices=None):
        try:
            destinations = [(to_address, amount)]
            account = self.wallet.accounts[account_index]
            # Pour sélectionner des subadresses précises :
            tx = self.wallet.transfer(
                destinations,
                account=account,
                subaddresses=subaddr_indices if subaddr_indices else None
            )
            logger.info(f"Transaction sent. TX Hash: {tx.hash}")
            return tx.hash
        except Exception as e:
            logger.error(f"Error sending transaction: {e}")
            return None

    def fetch_rates(self):
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': settings.X_CMC_PRO_API_KEY,
        }
        currencies = ['USD', 'BTC', 'EUR', 'CHF', 'RUB', 'CAD', 'CNY']
        session = requests.Session()
        session.headers.update(headers)
        for currency in currencies:
            params = {
                'symbol': 'XMR',
                'convert': currency
            }
            try:
                response = session.get(url, params=params, timeout=15)
                logger.info(f"CMC request URL: {response.url}")
                if response.status_code != 200:
                    logger.error(f"CMC ERROR {response.status_code}: {response.text}")
                    continue
                data = response.json()
                rate_data = data['data']['XMR']['quote'][currency]
                MoneroRate.objects.update_or_create(
                    currency=currency,
                    defaults={
                        'rate': rate_data['price'],
                        'inverse_rate': 1 / rate_data['price'] if rate_data['price'] else None
                    }
                )
            except Exception as e:
                logger.error(f"Exception fetching Monero rate for {currency}: {e}")

    def monitor_transactions(self, account_index=0):
        try:
            account = self.wallet.accounts[account_index]
            results = []
            for subaddress in account.subaddresses:
                idx = subaddress.index
                address = subaddress.address
                label = subaddress.label or ''
                balance = float(subaddress.balance)
                unlocked_balance = float(subaddress.unlocked_balance)
                txs = []
                for tx in subaddress.incoming():
                    txs.append({
                        'amount': float(tx.amount),
                        'txid': tx.hash,
                        'confirmations': tx.confirmations,
                        'status': 'unconfirmed' if tx.confirmations < 5 else 'confirmed'
                    })
                results.append({
                    'index': idx,
                    'address': address,
                    'label': label,
                    'balance': balance,
                    'unlocked_balance': unlocked_balance,
                    'transactions': txs
                })
            return results
        except Exception as e:
            logger.error(f"Error monitoring all transactions: {e}")
            return None

