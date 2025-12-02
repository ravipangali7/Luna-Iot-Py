"""
Public Vehicle URL Patterns
"""
from django.urls import path
from public_vehicle.views import public_vehicle_views

urlpatterns = [
    path('vehicles/', public_vehicle_views.get_public_vehicle_vehicles, name='get_public_vehicle_vehicles'),
    path('with-locations/', public_vehicle_views.get_all_public_vehicles_with_locations, name='get_all_public_vehicles_with_locations'),
    path('', public_vehicle_views.get_all_public_vehicles, name='get_all_public_vehicles'),
    path('<int:vehicle_id>/', public_vehicle_views.get_public_vehicle_by_id, name='get_public_vehicle_by_id'),
    path('by-institute/<int:institute_id>/', public_vehicle_views.get_public_vehicles_by_institute, name='get_public_vehicles_by_institute'),
    path('create/', public_vehicle_views.create_public_vehicle, name='create_public_vehicle'),
    path('<int:vehicle_id>/update/', public_vehicle_views.update_public_vehicle, name='update_public_vehicle'),
    path('<int:vehicle_id>/toggle-active/', public_vehicle_views.toggle_public_vehicle_active, name='toggle_public_vehicle_active'),
    path('<int:vehicle_id>/delete/', public_vehicle_views.delete_public_vehicle, name='delete_public_vehicle'),
]

