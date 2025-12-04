from django.urls import path
from vehicle_tag.views import vehicle_tag_views

urlpatterns = [
    # Generate tags
    path('generate/', vehicle_tag_views.generate_vehicle_tags, name='generate_vehicle_tags'),
    
    # List all tags (paginated)
    path('', vehicle_tag_views.get_all_vehicle_tags, name='get_all_vehicle_tags'),
    
    # Get tag by vtid
    path('<str:vtid>/', vehicle_tag_views.get_vehicle_tag_by_vtid, name='get_vehicle_tag_by_vtid'),
    
    # Get QR code image
    path('<str:vtid>/qr/', vehicle_tag_views.get_vehicle_tag_qr_image, name='get_vehicle_tag_qr_image'),
    
    # Create alert
    path('alert/', vehicle_tag_views.create_vehicle_tag_alert, name='create_vehicle_tag_alert'),
    
    # Bulk print
    path('bulk-print/', vehicle_tag_views.get_vehicle_tags_for_bulk_print, name='get_vehicle_tags_for_bulk_print'),
]

