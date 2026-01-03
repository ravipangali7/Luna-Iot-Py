"""
School SMS URL Patterns
"""
from django.urls import path
from school.views import school_sms_views

urlpatterns = [
    path('', school_sms_views.get_all_school_sms, name='get_all_school_sms'),
    path('<int:sms_id>/', school_sms_views.get_school_sms_by_id, name='get_school_sms_by_id'),
    path('by-institute/<int:institute_id>/', school_sms_views.get_school_sms_by_institute, name='get_school_sms_by_institute'),
    path('create/<int:institute_id>/', school_sms_views.create_school_sms, name='create_school_sms'),
    path('<int:sms_id>/update/', school_sms_views.update_school_sms, name='update_school_sms'),
    path('<int:sms_id>/delete/', school_sms_views.delete_school_sms, name='delete_school_sms'),
]

