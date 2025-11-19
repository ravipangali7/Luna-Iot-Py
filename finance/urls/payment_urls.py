"""
Payment URL Configuration
"""
from django.urls import path
from finance.views.payment_views import (
    initiate_payment,
    payment_callback,
    validate_payment,
    get_payment_transactions,
    get_payment_transaction_by_id,
)

urlpatterns = [
    # Initiate payment (create payment request)
    path('initiate/', initiate_payment, name='initiate_payment'),
    
    # Payment callback from ConnectIPS gateway
    path('callback/', payment_callback, name='payment_callback'),
    
    # Manual payment validation
    path('validate/', validate_payment, name='validate_payment'),
    
    # Get payment transactions (list)
    path('transactions/', get_payment_transactions, name='get_payment_transactions'),
    
    # Get payment transaction by ID
    path('transactions/<int:payment_id>/', get_payment_transaction_by_id, name='get_payment_transaction_by_id'),
]

