from datetime import datetime, timedelta
from django.utils import timezone
from device.models.status import Status
from device.models.location import Location


class VehicleStateService:
    """
    Service to calculate vehicle state based on latest status and location data.
    Matches the logic from Flutter VehicleService.getState() for consistency.
    """
    
    # State constants (matching Flutter)
    NO_DATA = 'nodata'
    INACTIVE = 'inactive'
    STOPPED = 'stop'
    IDLE = 'idle'
    RUNNING = 'running'
    OVERSPEED = 'overspeed'
    
    @staticmethod
    def get_vehicle_state(vehicle, latest_status=None, latest_location=None):
        """
        Calculate vehicle state based on latest status and location.
        
        Args:
            vehicle: Vehicle model instance
            latest_status: Latest Status instance (optional, will fetch if not provided)
            latest_location: Latest Location instance (optional, will fetch if not provided)
        
        Returns:
            str: Vehicle state ('nodata', 'inactive', 'stop', 'idle', 'running', 'overspeed')
        """
        # Fetch latest status if not provided
        if latest_status is None:
            try:
                latest_status = Status.objects.filter(imei=vehicle.imei).order_by('-createdAt').first()
            except Exception:
                latest_status = None
        
        # Fetch latest location if not provided
        if latest_location is None:
            try:
                latest_location = Location.objects.filter(imei=vehicle.imei).order_by('-createdAt').first()
            except Exception:
                latest_location = None
        
        # Check for no data condition (matching Flutter logic)
        # No data if: both are None, OR (ignition is None AND latitude is None)
        if (latest_status is None and latest_location is None) or \
           (latest_status is not None and latest_status.ignition is None and 
            latest_location is not None and latest_location.latitude is None):
            return VehicleStateService.NO_DATA
        
        # Check both status and location timestamps to find the most recent data
        most_recent_timestamp = None
        
        if latest_status is not None and latest_status.updatedAt is not None and \
           latest_location is not None and latest_location.updatedAt is not None:
            # Both exist, use the more recent one
            if latest_status.updatedAt > latest_location.updatedAt:
                most_recent_timestamp = latest_status.updatedAt
            else:
                most_recent_timestamp = latest_location.updatedAt
        elif latest_status is not None and latest_status.updatedAt is not None:
            # Only status exists
            most_recent_timestamp = latest_status.updatedAt
        elif latest_location is not None and latest_location.updatedAt is not None:
            # Only location exists
            most_recent_timestamp = latest_location.updatedAt
        
        # Check for inactive (no update in last 12 hours)
        if most_recent_timestamp is not None:
            now = timezone.now()
            # Ensure both are timezone-aware for comparison
            if timezone.is_naive(most_recent_timestamp):
                most_recent_timestamp = timezone.make_aware(most_recent_timestamp)
            
            difference = now - most_recent_timestamp
            
            if difference.total_seconds() > 12 * 3600:  # 12 hours in seconds
                return VehicleStateService.INACTIVE
        
        # Check ignition status
        if latest_status is not None and latest_status.ignition is False:
            return VehicleStateService.STOPPED
        
        if latest_status is not None and latest_status.ignition is True:
            # Check speed
            if latest_location is not None and latest_location.speed is not None:
                speed = int(latest_location.speed) if isinstance(latest_location.speed, (int, float)) else None
                
                if speed is not None and speed <= 5:
                    return VehicleStateService.IDLE
                
                if speed is not None and speed > 5:
                    # Check for overspeed
                    speed_limit = vehicle.speedLimit if hasattr(vehicle, 'speedLimit') else None
                    if speed_limit is not None:
                        try:
                            speed_limit_int = int(speed_limit) if isinstance(speed_limit, (int, float)) else None
                            if speed_limit_int is not None and speed_limit_int < speed:
                                return VehicleStateService.OVERSPEED
                        except (ValueError, TypeError):
                            pass
                    
                    return VehicleStateService.RUNNING
        
        return VehicleStateService.NO_DATA
    
    @staticmethod
    def map_filter_name_to_state(filter_name):
        """
        Map frontend filter name to backend state value.
        
        Args:
            filter_name: Filter name from frontend ('All', 'Running', 'Idle', etc.)
        
        Returns:
            str or None: State value or None for 'All'
        """
        mapping = {
            'All': None,
            'Running': VehicleStateService.RUNNING,
            'Idle': VehicleStateService.IDLE,
            'Stopped': VehicleStateService.STOPPED,
            'Overspeed': VehicleStateService.OVERSPEED,
            'Inactive': VehicleStateService.INACTIVE,
            'No Data': VehicleStateService.NO_DATA,
        }
        return mapping.get(filter_name, None)
