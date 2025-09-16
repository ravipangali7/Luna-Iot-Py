from django.urls import path
from health.views import blood_donation_views

urlpatterns = [
    path('blood-donation', blood_donation_views.get_all_blood_donations, name='get_all_blood_donations'),
    path('blood-donation/<int:id>', blood_donation_views.get_blood_donation_by_id, name='get_blood_donation_by_id'),
    path('blood-donation/create', blood_donation_views.create_blood_donation, name='create_blood_donation'),
    path('blood-donation/update/<int:id>', blood_donation_views.update_blood_donation, name='update_blood_donation'),
    path('blood-donation/delete/<int:id>', blood_donation_views.delete_blood_donation, name='delete_blood_donation'),
    path('blood-donation/type/<str:type>', blood_donation_views.get_blood_donations_by_type, name='get_blood_donations_by_type'),
    path('blood-donation/blood-group/<str:blood_group>', blood_donation_views.get_blood_donations_by_blood_group, name='get_blood_donations_by_blood_group'),
]
