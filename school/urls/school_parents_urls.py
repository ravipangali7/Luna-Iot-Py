"""
School Parents URL Patterns
"""
from django.urls import path
from school.views import school_parents_views

urlpatterns = [
    path('', school_parents_views.get_all_school_parents, name='get_all_school_parents'),
    path('my-vehicles/', school_parents_views.get_my_school_vehicles, name='get_my_school_vehicles'),
    path('<int:parent_id>/', school_parents_views.get_school_parent_by_id, name='get_school_parent_by_id'),
    path('by-institute/<int:institute_id>/', school_parents_views.get_school_parents_by_institute, name='get_school_parents_by_institute'),
    path('by-bus/<int:bus_id>/', school_parents_views.get_school_parents_by_bus, name='get_school_parents_by_bus'),
    path('create/', school_parents_views.create_school_parent, name='create_school_parent'),
    path('<int:parent_id>/update/', school_parents_views.update_school_parent, name='update_school_parent'),
    path('<int:parent_id>/delete/', school_parents_views.delete_school_parent, name='delete_school_parent'),
]

