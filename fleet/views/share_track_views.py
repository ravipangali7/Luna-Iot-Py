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
        share_track = get_object_or_404(ShareTrack, token=token, is_active=True)
        
        # Check if expired
        if share_track.is_expired():
            share_track.deactivate()
            return Response({
                'success': False,
                'message': 'Share track has expired'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get vehicle information with all related data
        try:
            vehicle = Vehicle.objects.select_related().prefetch_related(
                'latestLocation', 'latestStatus'
            ).get(imei=share_track.imei)
            
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
            
            # Add latest location if available
            if hasattr(vehicle, 'latestLocation') and vehicle.latestLocation:
                vehicle_data['latestLocation'] = {
                    'id': vehicle.latestLocation.id,
                    'imei': vehicle.latestLocation.imei,
                    'latitude': float(vehicle.latestLocation.latitude),
                    'longitude': float(vehicle.latestLocation.longitude),
                    'speed': float(vehicle.latestLocation.speed) if vehicle.latestLocation.speed else 0,
                    'course': float(vehicle.latestLocation.course) if vehicle.latestLocation.course else 0,
                    'satellite': float(vehicle.latestLocation.satellite) if vehicle.latestLocation.satellite else 0,
                    'realTimeGps': vehicle.latestLocation.realTimeGps,
                    'createdAt': vehicle.latestLocation.createdAt.isoformat() if vehicle.latestLocation.createdAt else None,
                    'updatedAt': vehicle.latestLocation.updatedAt.isoformat() if vehicle.latestLocation.updatedAt else None,
                }
            else:
                vehicle_data['latestLocation'] = None
                
            # Add latest status if available
            if hasattr(vehicle, 'latestStatus') and vehicle.latestStatus:
                vehicle_data['latestStatus'] = {
                    'id': vehicle.latestStatus.id,
                    'imei': vehicle.latestStatus.imei,
                    'battery': float(vehicle.latestStatus.battery) if vehicle.latestStatus.battery else 0,
                    'signal': float(vehicle.latestStatus.signal) if vehicle.latestStatus.signal else 0,
                    'ignition': vehicle.latestStatus.ignition,
                    'charging': vehicle.latestStatus.charging,
                    'relay': vehicle.latestStatus.relay,
                    'createdAt': vehicle.latestStatus.createdAt.isoformat() if vehicle.latestStatus.createdAt else None,
                    'updatedAt': vehicle.latestStatus.updatedAt.isoformat() if vehicle.latestStatus.updatedAt else None,
                }
            else:
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
