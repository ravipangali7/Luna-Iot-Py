from django.urls import path
from fleet.views import vehicle_views

urlpatterns = [
    # Main vehicle endpoints - specific patterns first
    path('vehicle', vehicle_views.get_all_vehicles, name='get_all_vehicles'),
    path('vehicle/detailed', vehicle_views.get_all_vehicles_detailed, name='get_all_vehicles_detailed'),
    path('vehicle/paginated', vehicle_views.get_vehicles_paginated, name='get_vehicles_paginated'),
    path('vehicle/search', vehicle_views.search_vehicles, name='search_vehicles'),
    path('vehicle/create', vehicle_views.create_vehicle, name='create_vehicle'),
    path('vehicle/update/<str:imei>', vehicle_views.update_vehicle, name='update_vehicle'),
    path('vehicle/delete/<str:imei>', vehicle_views.delete_vehicle, name='delete_vehicle'),
    
    # Vehicle access routes - must come before vehicle/<str:imei> to avoid conflicts
    path('vehicle/access', vehicle_views.assign_vehicle_access_to_user, name='assign_vehicle_access_to_user'),
    path('vehicle/access/available', vehicle_views.get_vehicles_for_access_assignment, name='get_vehicles_for_access_assignment'),
    path('vehicle/access/update', vehicle_views.update_vehicle_access, name='update_vehicle_access'),
    path('vehicle/access/remove', vehicle_views.remove_vehicle_access, name='remove_vehicle_access'),
    path('vehicle/<str:imei>/access', vehicle_views.get_vehicle_access_assignments, name='get_vehicle_access_assignments'),
    
    # This must come last to avoid conflicts with specific patterns above
    path('vehicle/<str:imei>', vehicle_views.get_vehicle_by_imei, name='get_vehicle_by_imei'),
]
