from django.urls import path
from . import views  # Si vous créez un fichier views.py plus tard, mettez vos vues ici
app_name = 'monero'

urlpatterns = [
    # Endpoint pour créer une sous-adresse utilisateur
    path('create-user-subaddress/', views.create_user_subaddress_view, name='create_user_subaddress'),
    
    # Endpoint pour créer une sous-adresse pour les frais
    path('create-fee-subaddress/', views.create_fee_subaddress_view, name='create_fee_subaddress'),
    
    # Endpoint pour créer une sous-adresse pour le séquestre (escrow)
    path('create-escrow-subaddress/', views.create_escrow_subaddress_view, name='create_escrow_subaddress'),
    
    # Endpoint pour consulter le solde d'une sous-adresse et ses transactions
    path('subaddress/<int:subaddress_index>/balance/', views.subaddress_balance_view, name='subaddress_balance'),
    
    # Endpoint pour envoyer des Monero
    path('send-xmr/', views.send_xmr_view, name='send_xmr'),
    
    # Endpoint pour récupérer les taux de change du Monero
    path('fetch-rates/', views.fetch_rates_view, name='fetch_rates'),
]


#from django.urls import path

#app_name = 'monero'

#urlpatterns = [
    
    #path('webhook/', views.webhook_view, name='webhook_view'),
#]
