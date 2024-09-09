from django.urls import path
from .views import transaction_list_view, transaction_detail_view, create_transaction_view

urlpatterns = [
    path('', transaction_list_view, name='transaction_list'),
    path('<int:pk>/', transaction_detail_view, name='transaction_detail'),
    path('create/<int:ad_pk>/', create_transaction_view, name='create_transaction'),
]
