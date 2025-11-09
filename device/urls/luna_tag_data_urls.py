"""
Luna Tag Data URL patterns
"""
from django.urls import path
from device.views import luna_tag_data_views

urlpatterns = [
    path('<str:publicKey>', luna_tag_data_views.get_luna_tag_data, name='get_luna_tag_data'),
]

