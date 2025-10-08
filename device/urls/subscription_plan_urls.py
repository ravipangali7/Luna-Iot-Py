from django.urls import path
from ..views.subscription_plan_views import (
    list_subscription_plans,
    get_subscription_plan,
    create_subscription_plan,
    update_subscription_plan,
    delete_subscription_plan,
    get_available_permissions
)

urlpatterns = [
    # Subscription Plan CRUD
    path('', list_subscription_plans, name='list_subscription_plans'),
    path('create/', create_subscription_plan, name='create_subscription_plan'),
    path('<int:plan_id>/', get_subscription_plan, name='get_subscription_plan'),
    path('<int:plan_id>/update/', update_subscription_plan, name='update_subscription_plan'),
    path('<int:plan_id>/delete/', delete_subscription_plan, name='delete_subscription_plan'),
    
    # Permissions
    path('permissions/', get_available_permissions, name='get_available_permissions'),
]
