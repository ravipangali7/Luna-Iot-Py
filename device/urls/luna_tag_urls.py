"""
Luna Tag URL patterns
"""
from django.urls import path
from device.views import luna_tag_views

urlpatterns = [
    path('', luna_tag_views.get_all_luna_tags, name='get_all_luna_tags'),
    path('create', luna_tag_views.create_luna_tag, name='create_luna_tag'),
    path('update/<int:id>', luna_tag_views.update_luna_tag, name='update_luna_tag'),
    path('delete/<int:id>', luna_tag_views.delete_luna_tag, name='delete_luna_tag'),
]

