"""
Notification Dispatcher

Coordinates notification services for dashcam location events.
Mimics the Node.js notification service pattern from gt06_handler.js.
"""
import logging
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)


class NotificationDispatcher:
    """
    Dispatches location events to various notification services.
    
    Services include:
    - Geofence checking
    - Speed limit monitoring
    - School bus proximity notifications
    - Public vehicle proximity notifications
    - Garbage vehicle proximity notifications
    - Firebase push notifications
    """
    
    def __init__(self):
        self._initialized = False
    
    async def dispatch_location_notifications(self, imei: str, latitude: float,
                                               longitude: float, speed: float,
                                               alarm_flags: int = 0) -> None:
        """
        Dispatch location-based notifications.
        
        This is called after saving location data to the database.
        Runs notification checks in the background (fire-and-forget).
        
        Args:
            imei: Device IMEI
            latitude: GPS latitude
            longitude: GPS longitude
            speed: Speed in km/h
            alarm_flags: JT808 alarm flags
        """
        # Fire-and-forget: run checks in background
        asyncio.create_task(self._run_notification_checks(
            imei, latitude, longitude, speed, alarm_flags
        ))
    
    async def _run_notification_checks(self, imei: str, latitude: float,
                                        longitude: float, speed: float,
                                        alarm_flags: int) -> None:
        """Run all notification checks."""
        try:
            # Run checks concurrently
            await asyncio.gather(
                self._check_geofence(imei, latitude, longitude),
                self._check_speed_limit(imei, speed),
                self._check_school_bus_proximity(imei, latitude, longitude),
                self._check_public_vehicle_proximity(imei, latitude, longitude),
                self._check_garbage_vehicle_proximity(imei, latitude, longitude),
                return_exceptions=True
            )
        except Exception as e:
            logger.error(f"[NotificationDispatcher] Error in checks for {imei}: {e}")
    
    async def _check_geofence(self, imei: str, latitude: float, 
                               longitude: float) -> None:
        """Check if device is inside/outside geofences."""
        try:
            from asgiref.sync import sync_to_async
            from device.models import Device
            from fleet.models import Geofence, GeofenceDevice
            
            # Get device
            device = await sync_to_async(
                Device.objects.filter(imei=imei).first,
                thread_sensitive=True
            )()
            
            if not device:
                return
            
            # Get geofences for this device's vehicles
            # This is a simplified version - full implementation would
            # check against polygon boundaries
            
            geofences = await sync_to_async(
                lambda: list(GeofenceDevice.objects.filter(
                    device__imei=imei
                ).select_related('geofence')),
                thread_sensitive=True
            )()
            
            for gf_device in geofences:
                geofence = gf_device.geofence
                # Check if point is inside geofence polygon
                # This would require implementing point-in-polygon algorithm
                # For now, just log
                logger.debug(f"[Geofence] Checking {imei} against {geofence.name}")
        
        except ImportError:
            pass  # Models not available
        except Exception as e:
            logger.error(f"[Geofence] Error checking {imei}: {e}")
    
    async def _check_speed_limit(self, imei: str, speed: float) -> None:
        """Check if device exceeds speed limit."""
        try:
            from asgiref.sync import sync_to_async
            from fleet.models import Vehicle
            
            # Get vehicle speed limit
            vehicle = await sync_to_async(
                lambda: Vehicle.objects.filter(device__imei=imei).first(),
                thread_sensitive=True
            )()
            
            if not vehicle or not vehicle.speed_limit:
                return
            
            if speed > vehicle.speed_limit:
                logger.info(f"[SpeedLimit] {imei} exceeding limit: {speed} > {vehicle.speed_limit}")
                # Here you would trigger an overspeeding notification
                # await self._send_speed_notification(imei, speed, vehicle.speed_limit)
        
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"[SpeedLimit] Error checking {imei}: {e}")
    
    async def _check_school_bus_proximity(self, imei: str, latitude: float,
                                          longitude: float) -> None:
        """Check school bus proximity to parent locations."""
        try:
            from asgiref.sync import sync_to_async
            from school.models import SchoolBus, SchoolParent
            
            # Check if this is a school bus
            school_bus = await sync_to_async(
                lambda: SchoolBus.objects.filter(vehicle__device__imei=imei).first(),
                thread_sensitive=True
            )()
            
            if not school_bus:
                return
            
            # Get parents for this school bus
            parents = await sync_to_async(
                lambda: list(SchoolParent.objects.filter(
                    school_bus=school_bus,
                    notification_enabled=True
                )),
                thread_sensitive=True
            )()
            
            for parent in parents:
                # Calculate distance
                distance = self._calculate_distance(
                    latitude, longitude,
                    parent.latitude, parent.longitude
                )
                
                # Check if within notification radius (e.g., 500m)
                if distance <= 0.5:  # km
                    logger.info(f"[SchoolBus] {imei} near parent {parent.id}: {distance:.2f}km")
                    # Trigger proximity notification
        
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"[SchoolBus] Error checking {imei}: {e}")
    
    async def _check_public_vehicle_proximity(self, imei: str, latitude: float,
                                               longitude: float) -> None:
        """Check public vehicle proximity to subscribers."""
        try:
            from asgiref.sync import sync_to_async
            from public_vehicle.models import PublicVehicle, PublicVehicleSubscriber
            
            # Check if this is a public vehicle
            public_vehicle = await sync_to_async(
                lambda: PublicVehicle.objects.filter(vehicle__device__imei=imei).first(),
                thread_sensitive=True
            )()
            
            if not public_vehicle:
                return
            
            # Get subscribers
            subscribers = await sync_to_async(
                lambda: list(PublicVehicleSubscriber.objects.filter(
                    public_vehicle=public_vehicle,
                    notification_enabled=True
                )),
                thread_sensitive=True
            )()
            
            for subscriber in subscribers:
                distance = self._calculate_distance(
                    latitude, longitude,
                    subscriber.latitude, subscriber.longitude
                )
                
                if distance <= 1.0:  # km
                    logger.info(f"[PublicVehicle] {imei} near subscriber: {distance:.2f}km")
        
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"[PublicVehicle] Error checking {imei}: {e}")
    
    async def _check_garbage_vehicle_proximity(self, imei: str, latitude: float,
                                                longitude: float) -> None:
        """Check garbage vehicle proximity to subscribers."""
        try:
            from asgiref.sync import sync_to_async
            from garbage.models import GarbageVehicle, GarbageSubscriber
            
            # Check if this is a garbage vehicle
            garbage_vehicle = await sync_to_async(
                lambda: GarbageVehicle.objects.filter(vehicle__device__imei=imei).first(),
                thread_sensitive=True
            )()
            
            if not garbage_vehicle:
                return
            
            # Get subscribers
            subscribers = await sync_to_async(
                lambda: list(GarbageSubscriber.objects.filter(
                    garbage_vehicle=garbage_vehicle,
                    notification_enabled=True
                )),
                thread_sensitive=True
            )()
            
            for subscriber in subscribers:
                distance = self._calculate_distance(
                    latitude, longitude,
                    subscriber.latitude, subscriber.longitude
                )
                
                if distance <= 0.3:  # km (300m)
                    logger.info(f"[Garbage] {imei} near subscriber: {distance:.2f}km")
        
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"[Garbage] Error checking {imei}: {e}")
    
    def _calculate_distance(self, lat1: float, lon1: float, 
                           lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula.
        
        Returns distance in kilometers.
        """
        import math
        
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c


# Global notification dispatcher instance
notification_dispatcher = NotificationDispatcher()
