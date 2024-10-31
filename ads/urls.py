from django.urls import path
from .views import ad_list_view, ad_detail_view, ad_create_view, ad_delete_view

app_name = 'ads'

urlpatterns = [
    path('', ad_list_view, name='ad_list'),  # Liste des annonces
    path('create/', ad_create_view, name='create_ad'),  # Créer une annonce
    path('<int:ad_id>/', ad_detail_view, name='ad_detail'),  # Détail d'une annonce
    path('<int:ad_id>/delete/', ad_delete_view, name='ad_delete'),  # Supprimer une annonce
]
