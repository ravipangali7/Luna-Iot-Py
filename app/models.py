from django.db import models
# Enums as choices
class GeofenceType(models.TextChoices):
    ENTRY = 'Entry', 'Entry'
    EXIT = 'Exit', 'Exit'

class NotificationType(models.TextChoices):
    ALL = 'all', 'All'
    SPECIFIC = 'specific', 'Specific'

class SimType(models.TextChoices):
    NTC = 'NTC', 'NTC'
    NCELL = 'Ncell', 'Ncell'

class ProtocolType(models.TextChoices):
    GT06 = 'GT06', 'GT06'
    FMB003 = 'FMB003', 'FMB003'

class DeviceModelType(models.TextChoices):
    EC08 = 'EC08', 'EC08'
    VL149 = 'VL149', 'VL149'

class VehicleType(models.TextChoices):
    AMBULANCE = 'Ambulance', 'Ambulance'
    BIKE = 'Bike', 'Bike'
    BOAT = 'Boat', 'Boat'
    BULLDOZER = 'Bulldozer', 'Bulldozer'
    BUS = 'Bus', 'Bus'
    CAR = 'Car', 'Car'
    CRANE = 'Crane', 'Crane'
    CYCLE = 'Cycle', 'Cycle'
    DUMPER = 'Dumper', 'Dumper'
    GARBAGE = 'Garbage', 'Garbage'
    JCB = 'Jcb', 'JCB'
    JEEP = 'Jeep', 'Jeep'
    MIXER = 'Mixer', 'Mixer'
    MPV = 'Mpv', 'MPV'
    PICKUP = 'Pickup', 'Pickup'
    SCHOOL_BUS = 'SchoolBus', 'School Bus'
    SUV = 'Suv', 'SUV'
    TANKER = 'Tanker', 'Tanker'
    TEMPO = 'Tempo', 'Tempo'
    TRACTOR = 'Tractor', 'Tractor'
    TRAIN = 'Train', 'Train'
    TRUCK = 'Truck', 'Truck'
    VAN = 'Van', 'Van'

class UserStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    INACTIVE = 'INACTIVE', 'Inactive'
    SUSPENDED = 'SUSPENDED', 'Suspended'

class PermissionType(models.TextChoices):
    # Device permissions
    DEVICE_READ = 'DEVICE_READ', 'Device Read'
    DEVICE_CREATE = 'DEVICE_CREATE', 'Device Create'
    DEVICE_UPDATE = 'DEVICE_UPDATE', 'Device Update'
    DEVICE_DELETE = 'DEVICE_DELETE', 'Device Delete'
    
    # Vehicle permissions
    VEHICLE_READ = 'VEHICLE_READ', 'Vehicle Read'
    VEHICLE_CREATE = 'VEHICLE_CREATE', 'Vehicle Create'
    VEHICLE_UPDATE = 'VEHICLE_UPDATE', 'Vehicle Update'
    VEHICLE_DELETE = 'VEHICLE_DELETE', 'Vehicle Delete'
    
    # Location permissions
    LOCATION_READ = 'LOCATION_READ', 'Location Read'
    LOCATION_HISTORY = 'LOCATION_HISTORY', 'Location History'
    
    # Status permissions
    STATUS_READ = 'STATUS_READ', 'Status Read'
    STATUS_HISTORY = 'STATUS_HISTORY', 'Status History'
    
    # User management permissions
    USER_READ = 'USER_READ', 'User Read'
    USER_CREATE = 'USER_CREATE', 'User Create'
    USER_UPDATE = 'USER_UPDATE', 'User Update'
    USER_DELETE = 'USER_DELETE', 'User Delete'
    
    # Role management permissions
    ROLE_READ = 'ROLE_READ', 'Role Read'
    ROLE_CREATE = 'ROLE_CREATE', 'Role Create'
    ROLE_UPDATE = 'ROLE_UPDATE', 'Role Update'
    ROLE_DELETE = 'ROLE_DELETE', 'Role Delete'
    
    # System permissions
    SYSTEM_ADMIN = 'SYSTEM_ADMIN', 'System Admin'
    DEVICE_MONITORING = 'DEVICE_MONITORING', 'Device Monitoring'
    LIVE_TRACKING = 'LIVE_TRACKING', 'Live Tracking'


class User(models.Model): 
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=255)
    token = models.CharField(max_length=500, unique=True, null=True, blank=True)
    fcm_token = models.CharField(max_length=500, null=True, blank=True)
    status = models.CharField(max_length=20, choices=UserStatus.choices, default=UserStatus.ACTIVE)
    role = models.ForeignKey('Role', on_delete=models.CASCADE, related_name='users', null=True)
    
    # Timestamps matching Prisma
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['phone', 'token', 'status']),
        ]

    def __str__(self):
        return f"{self.name} ({self.phone})"

    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_anonymous(self):
        return False

class Role(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'roles'

class Permission(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, choices=PermissionType.choices, unique=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'permissions'

class RolePermission(models.Model):
    id = models.BigAutoField(primary_key=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='roles')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['role', 'permission']
        db_table = 'role_permissions'

class Device(models.Model):
    id = models.BigAutoField(primary_key=True)
    imei = models.CharField(max_length=15, unique=True)
    phone = models.CharField(max_length=20)
    sim = models.CharField(max_length=10, choices=SimType.choices)
    protocol = models.CharField(max_length=10, choices=ProtocolType.choices, default=ProtocolType.GT06)
    iccid = models.CharField(max_length=255)
    model = models.CharField(max_length=10, choices=DeviceModelType.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'devices'

class Vehicle(models.Model):
    id = models.BigAutoField(primary_key=True)
    imei = models.CharField(max_length=15, unique=True)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='vehicles')
    name = models.CharField(max_length=255)
    vehicle_no = models.CharField(max_length=255)
    vehicle_type = models.CharField(max_length=20, choices=VehicleType.choices, default=VehicleType.CAR)
    odometer = models.DecimalField(max_digits=10, decimal_places=2)
    mileage = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_fuel = models.DecimalField(max_digits=10, decimal_places=2)
    speed_limit = models.IntegerField(default=60)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'vehicles'

class Location(models.Model):
    id = models.BigAutoField(primary_key=True)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='locations')
    imei = models.CharField(max_length=15)
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    speed = models.IntegerField()
    course = models.IntegerField()
    real_time_gps = models.BooleanField()
    satellite = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'locations'
        indexes = [
            models.Index(fields=['imei']),
            models.Index(fields=['created_at']),
            models.Index(fields=['latitude', 'longitude']),
        ]

class Status(models.Model):
    id = models.BigAutoField(primary_key=True)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='statuses')
    imei = models.CharField(max_length=15)
    battery = models.IntegerField()
    signal = models.IntegerField()
    ignition = models.BooleanField()
    charging = models.BooleanField()
    relay = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'statuses'
        indexes = [
            models.Index(fields=['imei']),
            models.Index(fields=['created_at']),
        ]

class UserDevice(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='userDevices')
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='userDevices')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'device']
        db_table = 'user_devices'

class UserVehicle(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='userVehicles')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='userVehicles')
    is_main = models.BooleanField(default=False)
    
    # Vehicle-specific permissions
    all_access = models.BooleanField(default=False)
    live_tracking = models.BooleanField(default=False)
    history = models.BooleanField(default=False)
    report = models.BooleanField(default=False)
    vehicle_profile = models.BooleanField(default=False)
    events = models.BooleanField(default=False)
    geofence = models.BooleanField(default=False)
    edit = models.BooleanField(default=False)
    share_tracking = models.BooleanField(default=False)
    notification = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'vehicle']
        db_table = 'user_vehicles'

class Otp(models.Model):
    id = models.BigAutoField(primary_key=True)
    phone = models.CharField(max_length=100)
    otp = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'otps'
        indexes = [
            models.Index(fields=['phone']),
        ]

class Notification(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=NotificationType.choices)
    sent_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sentNotifications')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        indexes = [
            models.Index(fields=['type', 'created_at']),
        ]

class UserNotification(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='userNotifications')
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='userNotifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'notification']
        db_table = 'user_notifications'
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]

class Geofence(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=GeofenceType.choices)
    boundary = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'geofences'

class GeofenceVehicle(models.Model):
    id = models.BigAutoField(primary_key=True)
    geofence = models.ForeignKey(Geofence, on_delete=models.CASCADE, related_name='vehicles')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='geofences')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['geofence', 'vehicle']
        db_table = 'geofence_vehicles'

class GeofenceUser(models.Model):
    id = models.BigAutoField(primary_key=True)
    geofence = models.ForeignKey(Geofence, on_delete=models.CASCADE, related_name='users')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='geofences')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['geofence', 'user']
        db_table = 'geofence_users'

class Popup(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    image = models.CharField(max_length=500, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'popups'