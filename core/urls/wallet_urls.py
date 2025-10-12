"""
Wallet URL Configuration
Handles wallet management endpoints
"""
from django.urls import path
from core.views import wallet_views

urlpatterns = [
    # List all wallets
    path('wallets', wallet_views.get_all_wallets, name='get_all_wallets'),
    
    # Create wallet
    path('wallet/create', wallet_views.create_wallet, name='create_wallet'),
    
    # Get wallet by user ID
    path('wallet/user/<int:user_id>', wallet_views.get_wallet_by_user, name='get_wallet_by_user'),
    
    # Wallet operations by ID - Django will route based on HTTP method
    path('wallet/<int:wallet_id>', wallet_views.wallet_by_id_handler, name='wallet_by_id_handler'),
    
    # Update wallet balance with operations (add, subtract, set)
    path('wallet/<int:wallet_id>/balance', wallet_views.update_wallet_balance_operation, name='update_wallet_balance_operation'),
]
