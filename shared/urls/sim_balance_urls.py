from django.urls import path
from shared.views import sim_balance_views

urlpatterns = [
    path('sim-balance/upload', sim_balance_views.upload_sim_data, name='upload_sim_data'),
    path('sim-balance', sim_balance_views.get_all_sim_balances, name='get_all_sim_balances'),
    path('sim-balance/paginated', sim_balance_views.get_sim_balances_with_pagination, name='get_sim_balances_with_pagination'),
    path('sim-balance/<int:id>', sim_balance_views.get_sim_balance_by_id, name='get_sim_balance_by_id'),
    path('sim-balance/device/<int:device_id>', sim_balance_views.get_sim_balance_by_device, name='get_sim_balance_by_device'),
    path('sim-balance/phone/<str:phone>', sim_balance_views.get_sim_balance_by_phone, name='get_sim_balance_by_phone'),
    path('sim-balance/<int:id>/delete', sim_balance_views.delete_sim_balance, name='delete_sim_balance'),
]

