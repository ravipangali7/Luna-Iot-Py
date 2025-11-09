"""
User Luna Tag URL patterns
"""
from django.urls import path
from device.views import user_luna_tag_views

urlpatterns = [
    path('', user_luna_tag_views.get_all_user_luna_tags, name='get_all_user_luna_tags'),
    path('create', user_luna_tag_views.create_user_luna_tag, name='create_user_luna_tag'),
    path('update/<int:id>', user_luna_tag_views.update_user_luna_tag, name='update_user_luna_tag'),
    path('delete/<int:id>', user_luna_tag_views.delete_user_luna_tag, name='delete_user_luna_tag'),
]

