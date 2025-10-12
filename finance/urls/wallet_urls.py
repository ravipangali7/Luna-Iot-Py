from django.urls import path
from finance.views import wallet_views

urlpatterns = [
    path('wallets', wallet_views.get_all_wallets, name='get_all_wallets'),
    path('wallet/user/<int:user_id>', wallet_views.get_wallet_by_user, name='get_wallet_by_user'),
    path('wallet/create', wallet_views.create_wallet, name='create_wallet'),
    path('wallet/<int:wallet_id>', wallet_views.get_wallet_by_id, name='get_wallet_by_id'),
    path('wallet/<int:wallet_id>/update', wallet_views.update_wallet_balance, name='update_wallet_balance'),
    path('wallet/<int:wallet_id>/operation', wallet_views.update_wallet_balance_operation, name='update_wallet_balance_operation'),
    path('wallet/<int:wallet_id>/topup', wallet_views.topup_wallet, name='topup_wallet'),
    path('wallet/<int:wallet_id>/delete', wallet_views.delete_wallet, name='delete_wallet'),
    path('summary', wallet_views.get_wallet_summary, name='get_wallet_summary'),
]