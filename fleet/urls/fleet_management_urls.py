from django.urls import path
from fleet.views import (
    vehicle_servicing_views,
    vehicle_expenses_views,
    vehicle_document_views,
    vehicle_energy_cost_views,
    fleet_report_views
)

urlpatterns = [
    # Vehicle Servicing endpoints
    path('vehicle/<str:imei>/servicing', vehicle_servicing_views.get_vehicle_servicings, name='get_vehicle_servicings'),
    path('vehicle/<str:imei>/servicing/create', vehicle_servicing_views.create_vehicle_servicing, name='create_vehicle_servicing'),
    path('vehicle/<str:imei>/servicing/<int:servicing_id>', vehicle_servicing_views.update_vehicle_servicing, name='update_vehicle_servicing'),
    path('vehicle/<str:imei>/servicing/<int:servicing_id>/delete', vehicle_servicing_views.delete_vehicle_servicing, name='delete_vehicle_servicing'),
    path('vehicle/<str:imei>/servicing/threshold', vehicle_servicing_views.check_servicing_threshold, name='check_servicing_threshold'),
    
    # Vehicle Expenses endpoints
    path('vehicle/<str:imei>/expenses', vehicle_expenses_views.get_vehicle_expenses, name='get_vehicle_expenses'),
    path('vehicle/<str:imei>/expenses/create', vehicle_expenses_views.create_vehicle_expense, name='create_vehicle_expense'),
    path('vehicle/<str:imei>/expenses/<int:expense_id>', vehicle_expenses_views.update_vehicle_expense, name='update_vehicle_expense'),
    path('vehicle/<str:imei>/expenses/<int:expense_id>/delete', vehicle_expenses_views.delete_vehicle_expense, name='delete_vehicle_expense'),
    
    # Vehicle Document endpoints
    path('vehicle/<str:imei>/documents', vehicle_document_views.get_vehicle_documents, name='get_vehicle_documents'),
    path('vehicle/<str:imei>/documents/create', vehicle_document_views.create_vehicle_document, name='create_vehicle_document'),
    path('vehicle/<str:imei>/documents/<int:document_id>', vehicle_document_views.update_vehicle_document, name='update_vehicle_document'),
    path('vehicle/<str:imei>/documents/<int:document_id>/delete', vehicle_document_views.delete_vehicle_document, name='delete_vehicle_document'),
    path('vehicle/<str:imei>/documents/<int:document_id>/renew', vehicle_document_views.renew_vehicle_document, name='renew_vehicle_document'),
    path('vehicle/<str:imei>/documents/<int:document_id>/renewal-threshold', vehicle_document_views.check_document_renewal_threshold, name='check_document_renewal_threshold'),
    
    # Vehicle Energy Cost endpoints
    path('vehicle/<str:imei>/energy-cost', vehicle_energy_cost_views.get_vehicle_energy_costs, name='get_vehicle_energy_costs'),
    path('vehicle/<str:imei>/energy-cost/create', vehicle_energy_cost_views.create_vehicle_energy_cost, name='create_vehicle_energy_cost'),
    path('vehicle/<str:imei>/energy-cost/<int:energy_cost_id>', vehicle_energy_cost_views.update_vehicle_energy_cost, name='update_vehicle_energy_cost'),
    path('vehicle/<str:imei>/energy-cost/<int:energy_cost_id>/delete', vehicle_energy_cost_views.delete_vehicle_energy_cost, name='delete_vehicle_energy_cost'),
    
    # Fleet Report endpoints
    path('vehicle/<str:imei>/report', fleet_report_views.get_vehicle_fleet_report, name='get_vehicle_fleet_report'),
    path('reports/all', fleet_report_views.get_all_vehicles_fleet_report, name='get_all_vehicles_fleet_report'),
    
    # All owned vehicles endpoints (grouped by vehicle)
    path('servicing/all-owned', vehicle_servicing_views.get_all_owned_vehicle_servicings, name='get_all_owned_vehicle_servicings'),
    path('expenses/all-owned', vehicle_expenses_views.get_all_owned_vehicle_expenses, name='get_all_owned_vehicle_expenses'),
    path('energy-cost/all-owned', vehicle_energy_cost_views.get_all_owned_vehicle_energy_costs, name='get_all_owned_vehicle_energy_costs'),
    path('documents/all-owned', vehicle_document_views.get_all_owned_vehicle_documents, name='get_all_owned_vehicle_documents'),
]

