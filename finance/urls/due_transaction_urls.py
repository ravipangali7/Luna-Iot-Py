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
    generate_due_transactions,
    delete_due_transaction,
    download_due_transaction_invoice,
    update_due_transaction,
)

urlpatterns = [
    # List all due transactions (Super Admin)
    path('', get_all_due_transactions, name='get_all_due_transactions'),
    
    # Create due transaction (Super Admin)
    path('create/', create_due_transaction, name='create_due_transaction'),
    
    # Get current user's due transactions
    path('my/', get_my_due_transactions, name='get_my_due_transactions'),
    
    # Generate due transactions (Super Admin)
    path('generate/', generate_due_transactions, name='generate_due_transactions'),
    
    # Get due transaction by ID
    path('<int:due_transaction_id>/', get_due_transaction_by_id, name='get_due_transaction_by_id'),
    
    # Update due transaction (Super Admin)
    path('<int:due_transaction_id>/update/', update_due_transaction, name='update_due_transaction'),
    
    # Pay due transaction with wallet
    path('<int:due_transaction_id>/pay/', pay_due_transaction_with_wallet, name='pay_due_transaction_with_wallet'),
    
    # Mark due transaction as paid (Super Admin)
    path('<int:due_transaction_id>/mark-paid/', mark_due_transaction_paid, name='mark_due_transaction_paid'),
    
    # Delete due transaction (Super Admin)
    path('<int:due_transaction_id>/delete/', delete_due_transaction, name='delete_due_transaction'),
    
    # Download invoice (PDF)
    path('<int:due_transaction_id>/invoice/', download_due_transaction_invoice, name='download_due_transaction_invoice'),
    
    # Get user's due transactions
    path('user/<int:user_id>/', get_user_due_transactions, name='get_user_due_transactions'),
]

