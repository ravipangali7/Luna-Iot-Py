from django.urls import path
from shared.views import banner_views

urlpatterns = [
    path('banner/active', banner_views.get_active_banners, name='get_active_banners'),
    path('banner/all', banner_views.get_all_banners, name='get_all_banners'),
    path('banner/<int:id>', banner_views.get_banner_by_id, name='get_banner_by_id'),
    path('banner/create', banner_views.create_banner, name='create_banner'),
    path('banner/update/<int:id>', banner_views.update_banner, name='update_banner'),
    path('banner/delete/<int:id>', banner_views.delete_banner, name='delete_banner'),
    path('banner/click/<int:id>', banner_views.increment_banner_click, name='increment_banner_click'),
]

