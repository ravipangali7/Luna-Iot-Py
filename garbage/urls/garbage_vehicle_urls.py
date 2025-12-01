"""
Garbage Vehicle URL Patterns
"""
from django.urls import path
from garbage.views import garbage_vehicle_views

urlpatterns = [
    path('vehicles/', garbage_vehicle_views.get_garbage_vehicle_vehicles, name='get_garbage_vehicle_vehicles'),
    path('with-locations/', garbage_vehicle_views.get_all_garbage_vehicles_with_locations, name='get_all_garbage_vehicles_with_locations'),
    path('', garbage_vehicle_views.get_all_garbage_vehicles, name='get_all_garbage_vehicles'),
    path('<int:vehicle_id>/', garbage_vehicle_views.get_garbage_vehicle_by_id, name='get_garbage_vehicle_by_id'),
    path('by-institute/<int:institute_id>/', garbage_vehicle_views.get_garbage_vehicles_by_institute, name='get_garbage_vehicles_by_institute'),
    path('create/', garbage_vehicle_views.create_garbage_vehicle, name='create_garbage_vehicle'),
    path('<int:vehicle_id>/update/', garbage_vehicle_views.update_garbage_vehicle, name='update_garbage_vehicle'),
    path('<int:vehicle_id>/delete/', garbage_vehicle_views.delete_garbage_vehicle, name='delete_garbage_vehicle'),
]

