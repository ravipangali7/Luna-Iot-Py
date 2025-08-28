from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'auth', views.AuthViewSet, basename='auth')
router.register(r'device', views.DeviceViewSet, basename='device')
router.register(r'vehicle', views.VehicleViewSet, basename='vehicle')
router.register(r'location', views.LocationViewSet, basename='location')
router.register(r'status', views.StatusViewSet, basename='status')
router.register(r'geofence', views.GeofenceViewSet, basename='geofence')
router.register(r'notification', views.NotificationViewSet, basename='notification')
router.register(r'popup', views.PopupViewSet, basename='popup')
router.register(r'user', views.UserViewSet, basename='user')
router.register(r'roles', views.RoleViewSet, basename='role')
router.register(r'relay', views.RelayViewSet, basename='relay')

urlpatterns = [
    path('api/', include(router.urls)),
    # Specific endpoints
    path('api/location/<str:imei>/', views.LocationViewSet.as_view({'get': 'get_by_imei'}), name='location_by_imei'),
    path('api/location/latest/<str:imei>/', views.LocationViewSet.as_view({'get': 'latest'}), name='location_latest'),
    path('api/location/range/<str:imei>/', views.LocationViewSet.as_view({'get': 'range'}), name='location_range'),
    path('api/location/combined/<str:imei>/', views.LocationViewSet.as_view({'get': 'combined'}), name='location_combined'),
    path('api/location/report/<str:imei>/', views.LocationViewSet.as_view({'get': 'report'}), name='location_report'),
    path('api/status/<str:imei>/', views.StatusViewSet.as_view({'get': 'get_by_imei'}), name='status_by_imei'),
    path('api/status/latest/<str:imei>/', views.StatusViewSet.as_view({'get': 'latest'}), name='status_latest'),
    path('api/status/range/<str:imei>/', views.StatusViewSet.as_view({'get': 'get_by_date_range'}), name='status_range'),
    path('api/device/<str:imei>/', views.DeviceViewSet.as_view({'get': 'get_by_imei'}), name='device_by_imei'),
    path('api/vehicle/<str:imei>/', views.VehicleViewSet.as_view({'get': 'get_by_imei'}), name='vehicle_by_imei'),
    path('api/geofence/vehicle/<str:imei>/', views.GeofenceViewSet.as_view({'get': 'get_by_imei'}), name='geofence_by_imei'),
    path('api/relay/status/<str:imei>/', views.RelayViewSet.as_view({'get': 'get_relay_status'}), name='relay_status'),
]