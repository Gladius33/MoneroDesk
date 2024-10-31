import os
import requests
from django.conf import settings
from monero.backends.jsonrpc import JSONRPCWallet
from .models import MoneroRate
import logging

logger = logging.getLogger(__name__)

class MoneroService:
    def __init__(self):
        self.rpc_wallet_url = f"http://{settings.XMR_RPC_HOST}:{settings.XMR_RPC_PORT}/json_rpc"
        self.wallet_rpc = JSONRPCWallet(self.rpc_wallet_url)
        self.wallet_directory = os.path.join(settings.BASE_DIR, 'XMR_WALLET')
        self.main_wallet_name = "XMR_WALLET"  # Nom du portefeuille principal

        # Créer ou ouvrir le portefeuille principal lors de l'initialisation
        self.check_or_create_main_wallet()

    def check_or_create_main_wallet(self):
        """
        Vérifie si le portefeuille principal Monero existe, et le crée si nécessaire.
        """
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
                logger.info("Portefeuille principal Monero créé avec succès.")
            except Exception as e:
                logger.error(f"Erreur lors de la création du portefeuille principal : {e}")
        else:
            logger.info("Le portefeuille principal Monero existe déjà.")
        
        self.wallet_rpc.open_wallet(wallet_name=self.main_wallet_name, password=settings.WALLET_PASS)

    def create_user_subaddress(self, label=None):
        """
        Crée une sous-adresse utilisateur pour les transactions.
        """
        wallet_pass = settings.WALLET_PASS
        try:
            self.wallet_rpc.open_wallet(wallet_name=self.main_wallet_name, password=wallet_pass)
            subaddress = self.wallet_rpc.create_address(account_index=0, label=label)
            logger.info(f"Sous-adresse Monero créée : {subaddress}")
            return subaddress
        except Exception as e:
            logger.error(f"Erreur lors de la création de la sous-adresse : {e}")
            return None

    def create_fee_subaddress(self, label=None):
        """
        Crée une sous-adresse dédiée aux frais pour les transactions.
        """
        wallet_pass = settings.WALLET_PASS
        try:
            self.wallet_rpc.open_wallet(wallet_name=self.main_wallet_name, password=wallet_pass)
            subaddress = self.wallet_rpc.create_address(account_index=1, label=label)
            logger.info(f"Sous-adresse de frais Monero créée : {subaddress}")
            return subaddress
        except Exception as e:
            logger.error(f"Erreur lors de la création de la sous-adresse de frais : {e}")
            return None

    def create_escrow_subaddress(self, label=None):
        """
        Crée une sous-adresse de séquestre pour les transactions.
        """
        wallet_pass = settings.WALLET_PASS
        try:
            self.wallet_rpc.open_wallet(wallet_name=self.main_wallet_name, password=wallet_pass)
            subaddress = self.wallet_rpc.create_address(account_index=2, label=label)
            logger.info(f"Sous-adresse de séquestre Monero créée : {subaddress}")
            return subaddress
        except Exception as e:
            logger.error(f"Erreur lors de la création de la sous-adresse de séquestre : {e}")
            return None

    def get_subaddress_balance_and_transactions(self, subaddress_index):
        """
        Récupère le solde et les transactions pour une sous-adresse spécifique.
        """
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
            logger.error(f"Erreur lors de la récupération du solde et des transactions : {e}")
            return None

    def send_xmr(self, to_address, amount, internal=False, fee=False, escrow=False):
        """
        Envoie des XMR à une adresse spécifiée.
        """
        try:
            self.wallet_rpc.open_wallet(wallet_name=self.main_wallet_name, password=settings.WALLET_PASS)
            amount_atomic = int(amount * 1e12)
            priority = 2
            destinations = [{'address': to_address, 'amount': amount_atomic}]
            
            if internal:
                if fee:
                    logger.info("Envoi vers la sous-adresse de frais")
                elif escrow:
                    logger.info("Envoi vers la sous-adresse de séquestre")
            else:
                tx_hash = self.wallet_rpc.transfer(destinations=destinations, priority=priority)
                logger.info(f"Transaction envoyée. Hash TX : {tx_hash}")
                return tx_hash
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la transaction : {e}")
            return None

    def monitor_all_transactions(self):
        """
        Monitore toutes les transactions en attente et met à jour leurs statuts et confirmations.
        """
        try:
            self.wallet_rpc.open_wallet(wallet_name=self.main_wallet_name, password=settings.WALLET_PASS)
            transfers = self.wallet_rpc.incoming_transfers(account_index=0)
            for transfer in transfers:
                txid = transfer['txid']
                confirmations = transfer['confirmations']
                status = 'confirmed' if confirmations >= 5 else 'unconfirmed'
                
                logger.info(f"Transaction {txid}: {status} avec {confirmations} confirmations.")
        except Exception as e:
            logger.error(f"Erreur lors du monitoring des transactions : {e}")

    def fetch_rates(self):
        """
        Récupère les taux de change de Monero depuis l'API et met à jour la base de données.
        """
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
        headers = {'X-CMC_PRO_API_KEY': settings.X_CMC_PRO_API_KEY}
        params = {'symbol': 'XMR', 'convert': 'USD,BTC,EUR,CHF,RUB,CAD,CNY'}
        
        try:
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
            logger.info("Taux de change Monero mis à jour avec succès.")
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des taux : {e}")
