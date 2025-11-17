"""
Due Transaction URL Configuration
"""
from django.urls import path
from finance.views.due_transaction_views import (
    get_all_due_transactions,
    get_due_transaction_by_id,
    get_user_due_transactions,
    pay_due_transaction_with_wallet,
    mark_due_transaction_paid,
    create_due_transaction,
    get_my_due_transactions,
)

urlpatterns = [
    # List all due transactions (Super Admin)
    path('', get_all_due_transactions, name='get_all_due_transactions'),
    
    # Create due transaction (Super Admin)
    path('create/', create_due_transaction, name='create_due_transaction'),
    
    # Get current user's due transactions
    path('my/', get_my_due_transactions, name='get_my_due_transactions'),
    
    # Get due transaction by ID
    path('<int:due_transaction_id>/', get_due_transaction_by_id, name='get_due_transaction_by_id'),
    
    # Pay due transaction with wallet
    path('<int:due_transaction_id>/pay/', pay_due_transaction_with_wallet, name='pay_due_transaction_with_wallet'),
    
    # Mark due transaction as paid (Super Admin)
    path('<int:due_transaction_id>/mark-paid/', mark_due_transaction_paid, name='mark_due_transaction_paid'),
    
    # Get user's due transactions
    path('user/<int:user_id>/', get_user_due_transactions, name='get_user_due_transactions'),
]

