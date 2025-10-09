from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
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
from core.views.auth_views import get_current_user

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
            }, status=status.HTTP_400_BAD_REQUEST)
        
        imei = serializer.validated_data['imei']
        duration_minutes = serializer.validated_data['duration_minutes']
        
        # Check if user has access to this vehicle
        user = request.user if hasattr(request, 'user') else get_current_user(request)
        try:
            vehicle = Vehicle.objects.get(imei=imei)
            # Add your vehicle access check here based on your permission system
            # For now, we'll assume the user has access if they can see the vehicle
        except Vehicle.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Vehicle not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
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
                }, status=status.HTTP_200_OK)
            
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
            }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        logger.error(f"Error creating share track: {str(e)}")
        return Response({
            'success': False,
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_existing_share_track(request, imei):
    """
    Get existing active share track for an IMEI
    """
    try:
        user = get_current_user(request)
        
        # Check if user has access to this vehicle
        try:
            vehicle = Vehicle.objects.get(imei=imei)
            # Add your vehicle access check here
        except Vehicle.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Vehicle not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
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
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if expired
        if share_track.is_expired():
            share_track.deactivate()
            return Response({
                'success': False,
                'message': 'Share track has expired'
            }, status=status.HTTP_404_NOT_FOUND)
        
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
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_share_track(request, imei):
    """
    Delete active share track for an IMEI
    """
    try:
        user = get_current_user(request)
        
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
            }, status=status.HTTP_404_NOT_FOUND)
        
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
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_share_tracks(request):
    """
    Get all share tracks for the current user
    """
    try:
        user = get_current_user(request)
        
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
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([])  # No authentication required for public access
def get_share_track_by_token(request, token):
    """
    Get share track by token (public endpoint for shared links)
    """
    try:
        # Get share track by token
        try:
            share_track = ShareTrack.objects.get(token=token, is_active=True)
        except ShareTrack.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Share track not found or has been deactivated'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if expired
        if share_track.is_expired():
            share_track.deactivate()
            return Response({
                'success': False,
                'message': 'Share track has expired'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get vehicle information
        try:
            vehicle = Vehicle.objects.get(imei=share_track.imei)
            
            # Check if vehicle is active
            if not vehicle.is_active:
                return Response({
                    'success': False,
                    'message': 'Vehicle has been deactivated'
                }, status=status.HTTP_404_NOT_FOUND)
            
            vehicle_data = {
                'id': vehicle.id,
                'imei': vehicle.imei,
                'vehicleNo': vehicle.vehicleNo,
                'name': vehicle.name,
                'vehicleType': vehicle.vehicleType,
                'odometer': float(vehicle.odometer) if vehicle.odometer else 0,
                'speedLimit': vehicle.speedLimit,
                'is_active': vehicle.is_active,
                'createdAt': vehicle.createdAt.isoformat() if vehicle.createdAt else None,
                'updatedAt': vehicle.updatedAt.isoformat() if vehicle.updatedAt else None,
            }
            
            # Get latest location from Location model
            try:
                from device.models import Location
                latest_location_obj = Location.objects.filter(imei=vehicle.imei).order_by('-createdAt').first()
                if latest_location_obj:
                    vehicle_data['latestLocation'] = {
                        'id': latest_location_obj.id,
                        'imei': latest_location_obj.imei,
                        'latitude': float(latest_location_obj.latitude),
                        'longitude': float(latest_location_obj.longitude),
                        'speed': float(latest_location_obj.speed) if latest_location_obj.speed else 0,
                        'course': float(latest_location_obj.course) if latest_location_obj.course else 0,
                        'satellite': float(latest_location_obj.satellite) if latest_location_obj.satellite else 0,
                        'realTimeGps': latest_location_obj.realTimeGps,
                        'createdAt': latest_location_obj.createdAt.isoformat() if latest_location_obj.createdAt else None,
                        'updatedAt': latest_location_obj.updatedAt.isoformat() if latest_location_obj.updatedAt else None,
                    }
                else:
                    vehicle_data['latestLocation'] = None
            except Exception as e:
                logger.warning(f"Error getting latest location: {str(e)}")
                vehicle_data['latestLocation'] = None
                
            # Get latest status from Status model
            try:
                from device.models import Status
                latest_status_obj = Status.objects.filter(imei=vehicle.imei).order_by('-createdAt').first()
                if latest_status_obj:
                    vehicle_data['latestStatus'] = {
                        'id': latest_status_obj.id,
                        'imei': latest_status_obj.imei,
                        'battery': float(latest_status_obj.battery) if latest_status_obj.battery else 0,
                        'signal': float(latest_status_obj.signal) if latest_status_obj.signal else 0,
                        'ignition': latest_status_obj.ignition,
                        'charging': latest_status_obj.charging,
                        'relay': latest_status_obj.relay,
                        'createdAt': latest_status_obj.createdAt.isoformat() if latest_status_obj.createdAt else None,
                        'updatedAt': latest_status_obj.updatedAt.isoformat() if latest_status_obj.updatedAt else None,
                    }
                else:
                    vehicle_data['latestStatus'] = None
            except Exception as e:
                logger.warning(f"Error getting latest status: {str(e)}")
                vehicle_data['latestStatus'] = None
        except Vehicle.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Vehicle not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Serialize share track data
        share_track_serializer = ShareTrackResponseSerializer(share_track)
        
        return Response({
            'success': True,
            'message': 'Share track retrieved successfully',
            'data': share_track_serializer.data,
            'vehicle': vehicle_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting share track by token: {str(e)}")
        return Response({
            'success': False,
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
