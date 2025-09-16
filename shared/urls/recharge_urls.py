from django.urls import path
from shared.views import recharge_views

urlpatterns = [
    path('recharge', recharge_views.get_all_recharges, name='get_all_recharges'),
    path('recharge/paginated', recharge_views.get_recharges_with_pagination, name='get_recharges_with_pagination'),
    path('recharge/<int:id>', recharge_views.get_recharge_by_id, name='get_recharge_by_id'),
    path('recharge/device/<int:device_id>', recharge_views.get_recharges_by_device_id, name='get_recharges_by_device_id'),
    path('recharge/create', recharge_views.create_recharge, name='create_recharge'),
    path('recharge/stats/<int:device_id>', recharge_views.get_recharge_stats, name='get_recharge_stats'),
    path('recharge/total/<int:device_id>', recharge_views.get_total_recharge, name='get_total_recharge'),
    path('recharge/delete/<int:id>', recharge_views.delete_recharge, name='delete_recharge'),
]
