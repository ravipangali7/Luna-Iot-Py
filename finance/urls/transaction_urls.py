from django.urls import path
from finance.views import transaction_views

urlpatterns = [
    path('transactions', transaction_views.get_all_transactions, name='get_all_transactions'),
    path('transaction/<int:transaction_id>', transaction_views.get_transaction_by_id, name='get_transaction_by_id'),
    path('wallet/<int:wallet_id>/transactions', transaction_views.get_wallet_transactions, name='get_wallet_transactions'),
    path('user/<int:user_id>/transactions', transaction_views.get_user_transactions, name='get_user_transactions'),
    path('transaction/create', transaction_views.create_transaction, name='create_transaction'),
    path('summary', transaction_views.get_transaction_summary, name='get_transaction_summary'),
]