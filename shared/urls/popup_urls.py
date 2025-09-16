from django.urls import path
from shared.views import popup_views

urlpatterns = [
    path('popup/active', popup_views.get_active_popups, name='get_active_popups'),
    path('popup/all', popup_views.get_all_popups, name='get_all_popups'),
    path('popup/<int:id>', popup_views.get_popup_by_id, name='get_popup_by_id'),
    path('popup/create', popup_views.create_popup, name='create_popup'),
    path('popup/update/<int:id>', popup_views.update_popup, name='update_popup'),
    path('popup/delete/<int:id>', popup_views.delete_popup, name='delete_popup'),
]
