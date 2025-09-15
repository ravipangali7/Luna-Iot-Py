from django.db import models

class BaseManager(models.Manager):
    """Base manager with common functionality"""
    
    def active(self):
        """Return only active records"""
        return self.filter(is_active=True)
    
    def inactive(self):
        """Return only inactive records"""
        return self.filter(is_active=False)

class DeviceManager(BaseManager):
    """Custom manager for Device model"""
    
    def online(self):
        """Return only online devices"""
        return self.filter(status='ONLINE')
    
    def offline(self):
        """Return only offline devices"""
        return self.filter(status='OFFLINE')
    
    def by_imei(self, imei):
        """Get device by IMEI"""
        return self.filter(imei=imei).first()

class VehicleManager(BaseManager):
    """Custom manager for Vehicle model"""
    
    def by_vehicle_type(self, vehicle_type):
        """Filter vehicles by type"""
        return self.filter(vehicleType=vehicle_type)
    
    def by_imei(self, imei):
        """Get vehicle by IMEI"""
        return self.filter(imei=imei).first()

class LocationManager(BaseManager):
    """Custom manager for Location model"""
    
    def latest_by_imei(self, imei):
        """Get latest location for a device"""
        return self.filter(imei=imei).order_by('-createdAt').first()
    
    def by_date_range(self, imei, start_date, end_date):
        """Get locations within date range"""
        return self.filter(
            imei=imei,
            createdAt__range=[start_date, end_date]
        ).order_by('createdAt')
