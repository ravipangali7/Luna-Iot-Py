"""
NTC M2M Portal URL Patterns
"""
from django.urls import path
from shared.views import ntc_m2m_views

urlpatterns = [
    path('ntc-m2m/fetch-report/', ntc_m2m_views.fetch_ntc_m2m_report, name='fetch_ntc_m2m_report'),
    path('ntc-m2m/report-status/<str:task_id>/', ntc_m2m_views.get_ntc_m2m_report_status, name='get_ntc_m2m_report_status'),
]

