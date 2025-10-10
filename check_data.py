#!/usr/bin/env python
import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'luna_iot_py.settings')
django.setup()

from device.models.location import Location
from device.models.status import Status

imei = "352312094630210"
print(f"Checking data for IMEI: {imei}")

# Check location data
location_count = Location.objects.filter(imei=imei).count()
print(f"Location count: {location_count}")

if location_count > 0:
    latest_location = Location.objects.filter(imei=imei).order_by('-createdAt').first()
    print(f"Latest location: {latest_location}")
    print(f"Location details: lat={latest_location.latitude}, lng={latest_location.longitude}")

# Check status data
status_count = Status.objects.filter(imei=imei).count()
print(f"Status count: {status_count}")

if status_count > 0:
    latest_status = Status.objects.filter(imei=imei).order_by('-createdAt').first()
    print(f"Latest status: {latest_status}")
    print(f"Status details: battery={latest_status.battery}, signal={latest_status.signal}")

# Check if there are any locations/statuses at all
total_locations = Location.objects.count()
total_statuses = Status.objects.count()
print(f"Total locations in database: {total_locations}")
print(f"Total statuses in database: {total_statuses}")

if total_locations > 0:
    sample_location = Location.objects.first()
    print(f"Sample location IMEI: {sample_location.imei}")

if total_statuses > 0:
    sample_status = Status.objects.first()
    print(f"Sample status IMEI: {sample_status.imei}")
