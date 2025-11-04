"""
School Bus URL Patterns
"""
from django.urls import path
from school.views import school_bus_views

urlpatterns = [
    path('vehicles/', school_bus_views.get_school_bus_vehicles, name='get_school_bus_vehicles'),
    path('', school_bus_views.get_all_school_buses, name='get_all_school_buses'),
    path('<int:bus_id>/', school_bus_views.get_school_bus_by_id, name='get_school_bus_by_id'),
    path('by-institute/<int:institute_id>/', school_bus_views.get_school_buses_by_institute, name='get_school_buses_by_institute'),
    path('create/', school_bus_views.create_school_bus, name='create_school_bus'),
    path('<int:bus_id>/update/', school_bus_views.update_school_bus, name='update_school_bus'),
    path('<int:bus_id>/delete/', school_bus_views.delete_school_bus, name='delete_school_bus'),
]

