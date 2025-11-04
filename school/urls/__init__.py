from django.urls import path, include

urlpatterns = [
    # School Bus routes
    path('school-bus/', include('school.urls.school_bus_urls')),
    
    # School Parents routes
    path('school-parents/', include('school.urls.school_parents_urls')),
    
    # School SMS routes
    path('school-sms/', include('school.urls.school_sms_urls')),
]

