from django.urls import path
from finance.views import wallet_views

urlpatterns = [
    path('wallets/', wallet_views.get_all_wallets, name='get_all_wallets'),
    path('user/<int:user_id>/', wallet_views.get_wallet_by_user, name='get_wallet_by_user'),
    path('create/', wallet_views.create_wallet, name='create_wallet'),
    path('<int:wallet_id>/', wallet_views.get_wallet_by_id, name='get_wallet_by_id'),
    path('<int:wallet_id>/update/', wallet_views.update_wallet_balance, name='update_wallet_balance'),
    path('<int:wallet_id>/operation/', wallet_views.update_wallet_balance_operation, name='update_wallet_balance_operation'),
    path('<int:wallet_id>/topup/', wallet_views.topup_wallet, name='topup_wallet'),
    path('<int:wallet_id>/delete/', wallet_views.delete_wallet, name='delete_wallet'),
    path('summary/', wallet_views.get_wallet_summary, name='get_wallet_summary'),
]