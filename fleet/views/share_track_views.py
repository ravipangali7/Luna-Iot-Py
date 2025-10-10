from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status as http_status
from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404
from datetime import timedelta
import logging

from fleet.models.share_track import ShareTrack
from fleet.models.vehicle import Vehicle
from fleet.serializers.share_track_serializers import (
    ShareTrackSerializer,
    ShareTrackCreateSerializer,
    ShareTrackResponseSerializer
)

logger = logging.getLogger(__name__)


@api_view(['POST'])
def create_share_track(request):
    """
    Create a new share track for a vehicle
    """
    logger.info(f"create_share_track called with method: {request.method}")
    logger.info(f"Request data: {request.data}")
    try:
        # Validate input data using serializer
        serializer = ShareTrackCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid input data.',
                'errors': serializer.errors
            }, status=http_status.HTTP_400_BAD_REQUEST)
        
        imei = serializer.validated_data['imei']
        duration_minutes = serializer.validated_data['duration_minutes']
        
        # Get authenticated user
        user = request.user
        if not user or not hasattr(user, 'id') or user.is_anonymous:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=http_status.HTTP_401_UNAUTHORIZED)
        try:
            vehicle = Vehicle.objects.get(imei=imei)
            
            # Check if user has access to this vehicle
            # Check if user is super admin or has access to this vehicle
            has_access = False
            
            # Super admin has access to all vehicles
            if hasattr(user, 'is_superuser') and user.is_superuser:
                has_access = True
            else:
                # Check if user has access through vehicle access permissions
                # This would depend on your vehicle access system
                # For now, we'll check if the user is associated with this vehicle
                if hasattr(vehicle, 'uservehicles') and vehicle.uservehicles:
                    # Check if current user is in the uservehicles list
                    for uv in vehicle.uservehicles:
                        if isinstance(uv, dict) and uv.get('userId') == user.id:
                            has_access = True
                            break
                        elif hasattr(uv, 'user_id') and uv.user_id == user.id:
                            has_access = True
                            break
            
            if not has_access:
                return Response({
                    'success': False,
                    'message': 'You do not have permission to share this vehicle'
                }, status=http_status.HTTP_403_FORBIDDEN)
                
        except Vehicle.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Vehicle not found'
            }, status=http_status.HTTP_404_NOT_FOUND)
        
        with transaction.atomic():
            # Check if there's already an active share track for this IMEI by this user
            existing_share = ShareTrack.objects.filter(
                imei=imei,
                user=user,
                is_active=True,
                scheduled_for__gt=timezone.now()  # Not expired
            ).first()
            
            if existing_share:
                # Return existing share track instead of creating a new one
                response_serializer = ShareTrackResponseSerializer(existing_share)
                return Response({
                    'success': True,
                    'message': 'Active share track already exists for this vehicle',
                    'data': response_serializer.data,
                    'token': existing_share.token,
                    'is_existing': True
                }, status=http_status.HTTP_200_OK)
            
            # Deactivate any expired share tracks for this IMEI by this user
            ShareTrack.objects.filter(
                imei=imei,
                user=user,
                is_active=True,
                scheduled_for__lte=timezone.now()  # Expired
            ).update(is_active=False)
            
            # Calculate scheduled_for time
            scheduled_for = timezone.now() + timedelta(minutes=duration_minutes)
            
            # Create new share track
            share_track = ShareTrack.objects.create(
                imei=imei,
                user=user,
                scheduled_for=scheduled_for
            )
            
            response_serializer = ShareTrackResponseSerializer(share_track)
            return Response({
                'success': True,
                'message': 'Share track created successfully',
                'data': response_serializer.data,
                'token': share_track.token,
                'is_existing': False
            }, status=http_status.HTTP_201_CREATED)
            
    except Exception as e:
        logger.error(f"Error creating share track: {str(e)}")
        return Response({
            'success': False,
            'message': 'Internal server error'
        }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_existing_share_track(request, imei):
    """
    Get existing active share track for an IMEI
    """
    try:
        # Get authenticated user
        user = request.user
        if not user or not hasattr(user, 'id') or user.is_anonymous:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=http_status.HTTP_401_UNAUTHORIZED)
        
        # Check if user has access to this vehicle
        try:
            vehicle = Vehicle.objects.get(imei=imei)
            
            # Check if user has access to this vehicle
            has_access = False
            
            # Super admin has access to all vehicles
            if hasattr(user, 'is_superuser') and user.is_superuser:
                has_access = True
            else:
                # Check if user has access through vehicle access permissions
                if hasattr(vehicle, 'uservehicles') and vehicle.uservehicles:
                    for uv in vehicle.uservehicles:
                        if isinstance(uv, dict) and uv.get('userId') == user.id:
                            has_access = True
                            break
                        elif hasattr(uv, 'user_id') and uv.user_id == user.id:
                            has_access = True
                            break
            
            if not has_access:
                return Response({
                    'success': False,
                    'message': 'You do not have permission to view this vehicle'
                }, status=http_status.HTTP_403_FORBIDDEN)
                
        except Vehicle.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Vehicle not found'
            }, status=http_status.HTTP_404_NOT_FOUND)
        
        # Get active share track for this IMEI and user
        share_track = ShareTrack.objects.filter(
            imei=imei,
            user=user,
            is_active=True
        ).first()
        
        if not share_track:
            return Response({
                'success': False,
                'message': 'No active share track found'
            }, status=http_status.HTTP_404_NOT_FOUND)
        
        # Check if expired
        if share_track.is_expired():
            share_track.deactivate()
            return Response({
                'success': False,
                'message': 'Share track has expired'
            }, status=http_status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'data': {
                'id': share_track.id,
                'imei': share_track.imei,
                'token': str(share_track.token),
                'created_at': share_track.created_at.isoformat(),
                'scheduled_for': share_track.scheduled_for.isoformat(),
                'duration_minutes': int((share_track.scheduled_for - share_track.created_at).total_seconds() / 60)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting existing share track: {str(e)}")
        return Response({
            'success': False,
            'message': 'Internal server error'
        }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_share_track(request, imei):
    """
    Delete active share track for an IMEI
    """
    try:
        # Get authenticated user
        user = request.user
        if not user or not hasattr(user, 'id') or user.is_anonymous:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=http_status.HTTP_401_UNAUTHORIZED)
        
        # Get active share track for this IMEI and user
        share_track = ShareTrack.objects.filter(
            imei=imei,
            user=user,
            is_active=True
        ).first()
        
        if not share_track:
            return Response({
                'success': False,
                'message': 'No active share track found'
            }, status=http_status.HTTP_404_NOT_FOUND)
        
        # Deactivate the share track
        share_track.deactivate()
        
        return Response({
            'success': True,
            'message': 'Share track deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting share track: {str(e)}")
        return Response({
            'success': False,
            'message': 'Internal server error'
        }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_share_tracks(request):
    """
    Get all share tracks for the current user
    """
    try:
        # Get authenticated user
        user = request.user
        if not user or not hasattr(user, 'id') or user.is_anonymous:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=http_status.HTTP_401_UNAUTHORIZED)
        
        share_tracks = ShareTrack.objects.filter(
            user=user,
            is_active=True
        ).order_by('-created_at')
        
        data = []
        for share_track in share_tracks:
            if not share_track.is_expired():
                data.append({
                    'id': share_track.id,
                    'imei': share_track.imei,
                    'token': str(share_track.token),
                    'created_at': share_track.created_at.isoformat(),
                    'scheduled_for': share_track.scheduled_for.isoformat(),
                    'duration_minutes': int((share_track.scheduled_for - share_track.created_at).total_seconds() / 60)
                })
            else:
                # Deactivate expired tracks
                share_track.deactivate()
        
        return Response({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        logger.error(f"Error getting my share tracks: {str(e)}")
        return Response({
            'success': False,
            'message': 'Internal server error'
        }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_share_track_by_token(request, token):
    """
    Get share track by token (public endpoint for shared links)
    """
    try:
        # Get share track by token - convert string to UUID for comparison
        try:
            import uuid
            token_uuid = uuid.UUID(token)
            share_track = ShareTrack.objects.get(token=token_uuid, is_active=True)
        except (ShareTrack.DoesNotExist, ValueError):
            return Response({
                'success': False,
                'message': 'Share track not found or has expired'
            }, status=http_status.HTTP_404_NOT_FOUND)
        
        # Check if expired
        if share_track.is_expired():
            share_track.deactivate()
            return Response({
                'success': False,
                'message': 'Share track has expired'
            }, status=http_status.HTTP_404_NOT_FOUND)
        
        # Get vehicle information
        try:
            from fleet.models.vehicle import Vehicle
            from device.models.location import Location
            from device.models.status import Status
            
            vehicle = Vehicle.objects.get(imei=share_track.imei)
            
            # Get latest location
            latest_location = None
            try:
                location = Location.objects.filter(imei=share_track.imei).order_by('-createdAt').first()
                if location:
                    latest_location = {
                        'id': location.id,
                        'imei': location.imei,
                        'latitude': float(location.latitude),
                        'longitude': float(location.longitude),
                        'speed': float(location.speed),
                        'course': float(location.course),
                        'satellite': float(location.satellite),
                        'realTimeGps': location.realTimeGps,
                        'createdAt': location.createdAt.isoformat()
                    }
            except Exception as e:
                logger.error(f"Error getting latest location: {e}")
            
            # Get latest status
            latest_status = None
            try:
                status = Status.objects.filter(imei=share_track.imei).order_by('-createdAt').first()
                if status:
                    latest_status = {
                        'id': status.id,
                        'imei': status.imei,
                        'battery': float(status.battery),
                        'signal': float(status.signal),
                        'ignition': status.ignition,
                        'charging': status.charging,
                        'relay': status.relay,
                        'createdAt': status.createdAt.isoformat()
                    }
            except Exception as e:
                logger.error(f"Error getting latest status: {e}")
            
            vehicle_data = {
                'imei': vehicle.imei,
                'vehicle_no': vehicle.vehicleNo,
                'name': vehicle.name,
                'vehicle_type': vehicle.vehicleType,
                'latest_location': latest_location,
                'latest_status': latest_status,
            }
        except Vehicle.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Vehicle not found'
            }, status=http_status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'data': {
                'share_track': {
                    'id': share_track.id,
                    'imei': share_track.imei,
                    'token': str(share_track.token),
                    'created_at': share_track.created_at.isoformat(),
                    'scheduled_for': share_track.scheduled_for.isoformat(),
                    'expires_in_minutes': int((share_track.scheduled_for - timezone.now()).total_seconds() / 60)
                },
                'vehicle': vehicle_data
            }
        }, status=http_status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        logger.error(f"Error getting share track by token: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'message': 'Internal server error'
        }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)
