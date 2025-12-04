from django.urls import path
from vehicle_tag.views import vehicle_tag_views

urlpatterns = [
    # Specific paths must come before generic <str:vtid> pattern
    
    # Generate tags
    path('generate/', vehicle_tag_views.generate_vehicle_tags, name='generate_vehicle_tags'),
    
    # Create alert
    path('alert/', vehicle_tag_views.create_vehicle_tag_alert, name='create_vehicle_tag_alert'),
    
    # Bulk print
    path('bulk-print/', vehicle_tag_views.get_vehicle_tags_for_bulk_print, name='get_vehicle_tags_for_bulk_print'),
    
    # Update and delete by ID (must come before <str:vtid> pattern)
    path('update/<int:id>/', vehicle_tag_views.update_vehicle_tag, name='update_vehicle_tag'),
    path('delete/<int:id>/', vehicle_tag_views.delete_vehicle_tag, name='delete_vehicle_tag'),
    
    # Get QR code image (must come before generic vtid pattern)
    path('<str:vtid>/qr/', vehicle_tag_views.get_vehicle_tag_qr_image, name='get_vehicle_tag_qr_image'),
    
    # Get tag by vtid (generic pattern - must be last)
    path('<str:vtid>/', vehicle_tag_views.get_vehicle_tag_by_vtid, name='get_vehicle_tag_by_vtid'),
    
    # List all tags (paginated) - must be last as it matches empty path
    path('', vehicle_tag_views.get_all_vehicle_tags, name='get_all_vehicle_tags'),
]

