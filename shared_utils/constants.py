from django.db import models

# Enums as choices
class GeofenceType(models.TextChoices):
    ENTRY = 'Entry', 'Entry'
    EXIT = 'Exit', 'Exit'

class NotificationType(models.TextChoices):
    ALL = 'all', 'All'
    SPECIFIC = 'specific', 'Specific'
    ROLE = 'role', 'Role'

class SimType(models.TextChoices):
    NTC = 'NTC', 'NTC'
    NCELL = 'Ncell', 'Ncell'

class ProtocolType(models.TextChoices):
    GT06 = 'GT06', 'GT06'
    FMB003 = 'FMB003', 'FMB003'

class DeviceModelType(models.TextChoices):
    EC08 = 'EC08', 'EC08'
    VL149 = 'VL149', 'VL149'

class DeviceType(models.TextChoices):
    GPS = 'gps', 'GPS'
    BUZZER = 'buzzer', 'Buzzer'
    SOS = 'sos', 'SOS'

class AlarmType(models.TextChoices):
    NORMAL = 'normal', 'Normal'
    SOS = 'sos', 'SOS'
    POWER_CUT = 'power_cut', 'Power Cut'
    SHOCK = 'shock', 'Shock'
    FENCE_IN = 'fence_in', 'Fence In'
    FENCE_OUT = 'fence_out', 'Fence Out'

class AlertSource(models.TextChoices):
    APP = 'app', 'App'
    GEOFENCE = 'geofence', 'Geofence'
    SWITCH = 'switch', 'Switch'

class AlertStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'

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


class BloodDonationApplyType(models.TextChoices):
    NEED = 'need', 'Need'
    DONATE = 'donate', 'Donate'

# OTP Configuration
OTP_EXPIRY_HOURS = 2
OTP_LENGTH = 6
