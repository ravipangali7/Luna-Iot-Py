"""
Device Order URL Configuration
"""
from django.urls import path
from ..views.device_order_views import (
    get_cart,
    add_to_cart,
    update_cart_item,
    remove_from_cart,
    clear_cart,
    create_order,
    list_orders,
    get_order,
    update_order_status,
    get_subscription_plans_for_order,
)

urlpatterns = [
    # Cart management routes
    path('cart/', get_cart, name='get_cart'),
    path('cart/add/', add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_index>/', update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_index>/', remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', clear_cart, name='clear_cart'),
    
    # Order management routes
    path('orders/create/', create_order, name='create_order'),
    path('orders/', list_orders, name='list_orders'),
    path('orders/<int:order_id>/', get_order, name='get_order'),
    path('orders/<int:order_id>/status/', update_order_status, name='update_order_status'),
    
    # Product listing for orders
    path('subscription-plans/for-order/', get_subscription_plans_for_order, name='get_subscription_plans_for_order'),
]

