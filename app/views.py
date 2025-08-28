from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
import bcrypt
import secrets
from .models import *
from .serializers import *

class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def send_registration_otp(self, request):
        phone = request.data.get('phone')
        if not phone:
            return Response({'success': False, 'message': 'Phone number is required'}, status=400)
        
        # Check if user exists
        if User.objects.filter(phone=phone).exists():
            return Response({'success': False, 'message': 'User already exists'}, status=400)
        
        # Generate OTP
        otp = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        # Save OTP
        OTP.objects.filter(phone=phone).delete()  # Remove old OTPs
        OTP.objects.create(
            phone=phone,
            otp=otp,
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        
        # TODO: Send SMS here
        return Response({
            'success': True,
            'data': {'phone': phone, 'message': 'OTP sent to your phone number'}
        })
    
    @action(detail=False, methods=['post'])
    def verify_otp_and_register(self, request):
        name = request.data.get('name')
        phone = request.data.get('phone')
        password = request.data.get('password')
        otp = request.data.get('otp')
        
        if not all([name, phone, password, otp]):
            return Response({'success': False, 'message': 'All fields are required'}, status=400)
        
        # Verify OTP
        try:
            otp_obj = OTP.objects.get(phone=phone, otp=otp, expires_at__gt=timezone.now())
        except OTP.DoesNotExist:
            return Response({'success': False, 'message': 'Invalid or expired OTP'}, status=400)
        
        # Get default role
        try:
            default_role = Role.objects.get(name='Customer')
        except Role.DoesNotExist:
            return Response({'success': False, 'message': 'Default role not found'}, status=500)
        
        # Create user
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12))
        token = secrets.token_hex(64)
        
        user = User.objects.create(
            username=phone,
            name=name,
            phone=phone,
            password=hashed_password.decode('utf-8'),
            token=token,
            role=default_role
        )
        
        # Delete OTP
        otp_obj.delete()
        
        return Response({
            'success': True,
            'data': {
                'id': user.id,
                'name': user.name,
                'phone': user.phone,
                'token': user.token,
                'role': user.role.name
            }
        }, status=201)
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        phone = request.data.get('phone')
        password = request.data.get('password')
        
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response({'success': False, 'message': 'User not found'}, status=404)
        
        # Check password
        if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            return Response({'success': False, 'message': 'Invalid credentials'}, status=401)
        
        # Generate new token
        token = secrets.token_hex(64)
        user.token = token
        user.save()
        
        return Response({
            'success': True,
            'data': {
                'id': user.id,
                'name': user.name,
                'phone': user.phone,
                'token': user.token,
                'role': user.role.name
            }
        })

    @action(detail=False, methods=['post'])
    def logout(self, request):
        # Get user from token
        phone = request.headers.get('x-phone')
        token = request.headers.get('x-token')
        
        if not phone or not token:
            return Response({'success': False, 'message': 'Phone and token required'}, status=401)
        
        try:
            user = User.objects.get(phone=phone, token=token, status='ACTIVE')
            user.token = None
            user.save()
            return Response({'success': True, 'message': 'Logout successful'})
        except User.DoesNotExist:
            return Response({'success': False, 'message': 'Invalid token or phone'}, status=777)

    @action(detail=False, methods=['get'])
    def me(self, request):
        # Get user from token
        phone = request.headers.get('x-phone')
        token = request.headers.get('x-token')
        
        if not phone or not token:
            return Response({'success': False, 'message': 'Phone and token required'}, status=401)
        
        try:
            user = User.objects.get(phone=phone, token=token, status='ACTIVE')
            return Response({
                'success': True,
                'data': {
                    'id': user.id,
                    'name': user.name,
                    'phone': user.phone,
                    'status': user.status,
                    'role': user.role.name,
                    'createdAt': user.created_at,
                    'updatedAt': user.updated_at
                }
            })
        except User.DoesNotExist:
            return Response({'success': False, 'message': 'Invalid token or phone'}, status=777)

    @action(detail=False, methods=['post'])
    def resend_otp(self, request):
        phone = request.data.get('phone')
        if not phone:
            return Response({'success': False, 'message': 'Phone number is required'}, status=400)
        
        # Check if user already exists
        if User.objects.filter(phone=phone).exists():
            return Response({'success': False, 'message': 'User already exists'}, status=400)
        
        # Generate new OTP
        otp = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        # Save OTP
        OTP.objects.filter(phone=phone).delete()  # Remove old OTPs
        OTP.objects.create(
            phone=phone,
            otp=otp,
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        
        # TODO: Send SMS here
        return Response({
            'success': True,
            'data': {'phone': phone, 'message': 'New OTP sent to your phone number'}
        })

    @action(detail=False, methods=['post'])
    def send_forgot_password_otp(self, request):
        phone = request.data.get('phone')
        if not phone:
            return Response({'success': False, 'message': 'Phone number is required'}, status=400)
        
        # Check if user exists
        if not User.objects.filter(phone=phone).exists():
            return Response({'success': False, 'message': 'User not found with this phone number'}, status=404)
        
        # Generate OTP
        otp = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        # Save OTP
        OTP.objects.filter(phone=phone).delete()  # Remove old OTPs
        OTP.objects.create(
            phone=phone,
            otp=otp,
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        
        # TODO: Send SMS here
        return Response({
            'success': True,
            'data': {'phone': phone, 'message': 'OTP sent to your phone number'}
        })

    @action(detail=False, methods=['post'])
    def verify_forgot_password_otp(self, request):
        phone = request.data.get('phone')
        otp = request.data.get('otp')
        
        if not phone or not otp:
            return Response({'success': False, 'message': 'Phone number and OTP are required'}, status=400)
        
        # Check if user exists
        if not User.objects.filter(phone=phone).exists():
            return Response({'success': False, 'message': 'User not found'}, status=404)
        
        # Verify OTP
        try:
            otp_obj = OTP.objects.get(phone=phone, otp=otp, expires_at__gt=timezone.now())
        except OTP.DoesNotExist:
            return Response({'success': False, 'message': 'Invalid or expired OTP'}, status=400)
        
        # Generate reset token
        reset_token = secrets.token_hex(64)
        
        # Update user with reset token
        user = User.objects.get(phone=phone)
        user.token = reset_token
        user.save()
        
        return Response({
            'success': True,
            'data': {
                'phone': phone,
                'resetToken': reset_token
            }
        })

    @action(detail=False, methods=['post'])
    def reset_password(self, request):
        phone = request.data.get('phone')
        reset_token = request.data.get('resetToken')
        new_password = request.data.get('newPassword')
        
        if not all([phone, reset_token, new_password]):
            return Response({'success': False, 'message': 'Phone number, reset token, and new password are required'}, status=400)
        
        # Check if user exists
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response({'success': False, 'message': 'User not found'}, status=404)
        
        # Verify reset token
        if user.token != reset_token:
            return Response({'success': False, 'message': 'Invalid reset token'}, status=400)
        
        # Hash new password
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt(12))
        
        # Generate new token
        new_token = secrets.token_hex(64)
        
        # Update user
        user.password = hashed_password.decode('utf-8')
        user.token = new_token
        user.save()
        
        # Delete OTP
        OTP.objects.filter(phone=phone).delete()
        
        return Response({
            'success': True,
            'data': {
                'id': user.id,
                'name': user.name,
                'phone': user.phone,
                'token': user.token,
                'role': user.role.name
            }
        })

class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role.name == 'Super Admin':
            return Device.objects.all()
        elif user.role.name == 'Dealer':
            return Device.objects.filter(userdevice__user=user)
        else:
            return Device.objects.none()
    
    @action(detail=False, methods=['post'])
    def assign(self, request):
        imei = request.data.get('imei')
        user_phone = request.data.get('userPhone')
        
        if not all([imei, user_phone]):
            return Response({'success': False, 'message': 'IMEI and user phone are required'}, status=400)
        
        try:
            device = Device.objects.get(imei=imei)
            target_user = User.objects.get(phone=user_phone)
        except (Device.DoesNotExist, User.DoesNotExist):
            return Response({'success': False, 'message': 'Device or user not found'}, status=404)
        
        if target_user.role.name != 'Dealer':
            return Response({'success': False, 'message': 'Only dealers can be assigned devices'}, status=400)
        
        # Create assignment
        UserDevice.objects.get_or_create(user=target_user, device=device)
        
        return Response({'success': True, 'message': 'Device assigned successfully'})

    @action(detail=False, methods=['delete'])
    def remove_assignment(self, request):
        imei = request.data.get('imei')
        user_phone = request.data.get('userPhone')
        
        if not all([imei, user_phone]):
            return Response({'success': False, 'message': 'IMEI and user phone are required'}, status=400)
        
        try:
            device = Device.objects.get(imei=imei)
            target_user = User.objects.get(phone=user_phone)
        except (Device.DoesNotExist, User.DoesNotExist):
            return Response({'success': False, 'message': 'Device or user not found'}, status=404)
        
        # Remove assignment
        deleted_count, _ = UserDevice.objects.filter(user=target_user, device=device).delete()
        
        if deleted_count > 0:
            return Response({'success': True, 'message': 'Device assignment removed successfully'})
        else:
            return Response({'success': False, 'message': 'Device assignment not found'}, status=404)

    @action(detail=False, methods=['get'])
    def get_by_imei(self, request, imei=None):
        if not imei:
            return Response({'success': False, 'message': 'IMEI is required'}, status=400)
        
        user = self.request.user
        
        if user.role.name == 'Super Admin':
            device = Device.objects.filter(imei=imei).first()
        elif user.role.name == 'Dealer':
            device = Device.objects.filter(
                imei=imei,
                userdevice__user=user
            ).first()
        else:
            device = None
        
        if not device:
            return Response({'success': False, 'message': 'Device not found or access denied'}, status=404)
        
        serializer = self.get_serializer(device)
        return Response({'success': True, 'data': serializer.data, 'message': 'Device retrieved successfully'})

class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        context = {'user_id': user.id}
        
        if user.role.name == 'Super Admin':
            return Vehicle.objects.all()
        elif user.role.name == 'Dealer':
            # Get vehicles from assigned devices + directly assigned vehicles
            device_imeis = Device.objects.filter(userdevice__user=user).values_list('imei', flat=True)
            direct_vehicles = Vehicle.objects.filter(uservehicle__user=user)
            device_vehicles = Vehicle.objects.filter(imei__in=device_imeis)
            
            all_vehicles = list(direct_vehicles) + list(device_vehicles)
            # Remove duplicates
            seen = set()
            unique_vehicles = []
            for v in all_vehicles:
                if v.id not in seen:
                    seen.add(v.id)
                    unique_vehicles.append(v)
            return unique_vehicles
        else:
            return Vehicle.objects.filter(uservehicle__user=user)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user_id'] = self.request.user.id
        return context

    @action(detail=False, methods=['get'])
    def get_by_imei(self, request, imei=None):
        if not imei:
            return Response({'success': False, 'message': 'IMEI is required'}, status=400)
        
        user = self.request.user
        
        if user.role.name == 'Super Admin':
            vehicle = Vehicle.objects.filter(imei=imei).first()
        elif user.role.name == 'Dealer':
            # Check if vehicle is directly assigned to dealer
            direct_vehicle = Vehicle.objects.filter(
                imei=imei,
                uservehicle__user=user
            ).first()
            
            if direct_vehicle:
                vehicle = direct_vehicle
            else:
                # Check if vehicle belongs to a device assigned to dealer
                vehicle = Vehicle.objects.filter(
                    imei=imei,
                    device__userdevice__user=user
                ).first()
        else:
            vehicle = Vehicle.objects.filter(
                imei=imei,
                uservehicle__user=user
            ).first()
        
        if not vehicle:
            return Response({'success': False, 'message': 'Vehicle not found or access denied'}, status=404)
        
        # Get complete data for the vehicle
        latest_status = Status.objects.filter(imei=imei).order_by('-created_at').first()
        latest_location = Location.objects.filter(imei=imei).order_by('-created_at').first()
        user_vehicle = UserVehicle.objects.filter(vehicle=vehicle, user=user).first()
        
        # Calculate today's kilometers (simplified)
        today_km = 0.0  # TODO: Implement actual calculation
        
        # Determine ownership type
        ownership_type = 'Customer'
        if user_vehicle:
            ownership_type = 'Own' if user_vehicle.is_main else 'Shared'
        
        vehicle_data = self.get_serializer(vehicle).data
        vehicle_data.update({
            'latestStatus': {
                'battery': latest_status.battery,
                'signal': latest_status.signal,
                'ignition': latest_status.ignition,
                'charging': latest_status.charging,
                'relay': latest_status.relay,
                'createdAt': latest_status.created_at
            } if latest_status else None,
            'latestLocation': {
                'latitude': latest_location.latitude,
                'longitude': latest_location.longitude,
                'speed': latest_location.speed,
                'createdAt': latest_location.created_at
            } if latest_location else None,
            'todayKm': today_km,
            'ownershipType': ownership_type,
            'userVehicle': {
                'isMain': user_vehicle.is_main,
                'allAccess': user_vehicle.all_access,
                'liveTracking': user_vehicle.live_tracking,
                'history': user_vehicle.history,
                'report': user_vehicle.report,
                'vehicleProfile': user_vehicle.vehicle_profile,
                'events': user_vehicle.events,
                'geofence': user_vehicle.geofence,
                'edit': user_vehicle.edit,
                'shareTracking': user_vehicle.share_tracking,
                'notification': user_vehicle.notification
            } if user_vehicle else None
        })
        
        return Response({'success': True, 'data': vehicle_data, 'message': 'Vehicle retrieved successfully'})

    @action(detail=False, methods=['post'])
    def assign_vehicle_access_to_user(self, request):
        imei = request.data.get('imei')
        user_phone = request.data.get('userPhone')
        permissions = request.data.get('permissions')
        
        if not all([imei, user_phone, permissions]):
            return Response({'success': False, 'message': 'IMEI, user phone, and permissions are required'}, status=400)
        
        try:
            vehicle = Vehicle.objects.get(imei=imei)
            target_user = User.objects.get(phone=user_phone)
        except (Vehicle.DoesNotExist, User.DoesNotExist):
            return Response({'success': False, 'message': 'Vehicle or user not found'}, status=404)
        
        # Check if user has permission to assign access
        user = self.request.user
        if user.role.name != 'Super Admin':
            main_user_vehicle = UserVehicle.objects.filter(
                vehicle=vehicle,
                user=user,
                is_main=True
            ).first()
            
            if not main_user_vehicle:
                return Response({'success': False, 'message': 'Access denied. Only main user or Super Admin can assign access'}, status=403)
        
        # Check if assignment already exists
        if UserVehicle.objects.filter(user=target_user, vehicle=vehicle).exists():
            return Response({'success': False, 'message': 'Vehicle access is already assigned to this user'}, status=400)
        
        # Create assignment with permissions
        assignment = UserVehicle.objects.create(
            user=target_user,
            vehicle=vehicle,
            is_main=False,
            all_access=permissions.get('allAccess', False),
            live_tracking=permissions.get('liveTracking', False),
            history=permissions.get('history', False),
            report=permissions.get('report', False),
            vehicle_profile=permissions.get('vehicleProfile', False),
            events=permissions.get('events', False),
            geofence=permissions.get('geofence', False),
            edit=permissions.get('edit', False),
            share_tracking=permissions.get('shareTracking', False),
            notification=permissions.get('notification', False)
        )
        
        return Response({'success': True, 'data': assignment, 'message': 'Vehicle access assigned successfully'})

    @action(detail=False, methods=['get'])
    def get_vehicles_for_access_assignment(self, request):
        user = self.request.user
        
        if user.role.name == 'Super Admin':
            vehicles = Vehicle.objects.all()
        else:
            # Users can only assign access to vehicles where they are the main user
            vehicles = Vehicle.objects.filter(
                uservehicle__user=user,
                uservehicle__is_main=True
            )
        
        serializer = self.get_serializer(vehicles, many=True)
        return Response({'success': True, 'data': serializer.data, 'message': 'Vehicles for access assignment retrieved successfully'})

    @action(detail=False, methods=['get'])
    def get_vehicle_access_assignments(self, request, imei=None):
        if not imei:
            return Response({'success': False, 'message': 'IMEI is required'}, status=400)
        
        user = self.request.user
        
        # Check if user has permission to view assignments
        if user.role.name != 'Super Admin':
            main_user_vehicle = UserVehicle.objects.filter(
                vehicle__imei=imei,
                user=user,
                is_main=True
            ).first()
            
            if not main_user_vehicle:
                return Response({'success': False, 'message': 'Access denied. Only main user or Super Admin can view assignments'}, status=403)
        
        # Get assignments for this vehicle (only shared access, not main ownership)
        assignments = UserVehicle.objects.filter(
            vehicle__imei=imei,
            is_main=False
        ).select_related('user', 'user__role')
        
        data = []
        for assignment in assignments:
            data.append({
                'id': assignment.id,
                'user': {
                    'id': assignment.user.id,
                    'name': assignment.user.name,
                    'phone': assignment.user.phone,
                    'role': {'name': assignment.user.role.name}
                },
                'vehicle': {
                    'id': assignment.vehicle.id,
                    'imei': assignment.vehicle.imei,
                    'name': assignment.vehicle.name
                },
                'permissions': {
                    'allAccess': assignment.all_access,
                    'liveTracking': assignment.live_tracking,
                    'history': assignment.history,
                    'report': assignment.report,
                    'vehicleProfile': assignment.vehicle_profile,
                    'events': assignment.events,
                    'geofence': assignment.geofence,
                    'edit': assignment.edit,
                    'shareTracking': assignment.share_tracking,
                    'notification': assignment.notification
                }
            })
        
        return Response({'success': True, 'data': data, 'message': 'Vehicle access assignments retrieved successfully'})

    @action(detail=False, methods=['put'])
    def update_vehicle_access(self, request):
        imei = request.data.get('imei')
        user_id = request.data.get('userId')
        permissions = request.data.get('permissions')
        
        if not all([imei, user_id, permissions]):
            return Response({'success': False, 'message': 'IMEI, user ID, and permissions are required'}, status=400)
        
        user = self.request.user
        
        # Check if user has permission to update access
        if user.role.name != 'Super Admin':
            main_user_vehicle = UserVehicle.objects.filter(
                vehicle__imei=imei,
                user=user,
                is_main=True
            ).first()
            
            if not main_user_vehicle:
                return Response({'success': False, 'message': 'Access denied. Only main user or Super Admin can update access'}, status=403)
        
        try:
            assignment = UserVehicle.objects.get(
                vehicle__imei=imei,
                user_id=user_id
            )
        except UserVehicle.DoesNotExist:
            return Response({'success': False, 'message': 'Vehicle access assignment not found'}, status=404)
        
        # Update permissions
        assignment.all_access = permissions.get('allAccess', False)
        assignment.live_tracking = permissions.get('liveTracking', False)
        assignment.history = permissions.get('history', False)
        assignment.report = permissions.get('report', False)
        assignment.vehicle_profile = permissions.get('vehicleProfile', False)
        assignment.events = permissions.get('events', False)
        assignment.geofence = permissions.get('geofence', False)
        assignment.edit = permissions.get('edit', False)
        assignment.share_tracking = permissions.get('shareTracking', False)
        assignment.notification = permissions.get('notification', False)
        assignment.save()
        
        return Response({'success': True, 'data': assignment, 'message': 'Vehicle access updated successfully'})

    @action(detail=False, methods=['delete'])
    def remove_vehicle_access(self, request):
        imei = request.data.get('imei')
        user_id = request.data.get('userId')
        
        if not all([imei, user_id]):
            return Response({'success': False, 'message': 'IMEI and user ID are required'}, status=400)
        
        user = self.request.user
        
        # Check if user has permission to remove access
        if user.role.name != 'Super Admin':
            main_user_vehicle = UserVehicle.objects.filter(
                vehicle__imei=imei,
                user=user,
                is_main=True
            ).first()
            
            if not main_user_vehicle:
                return Response({'success': False, 'message': 'Access denied. Only main user or Super Admin can remove access'}, status=403)
        
        try:
            assignment = UserVehicle.objects.get(
                vehicle__imei=imei,
                user_id=user_id
            )
            assignment.delete()
            return Response({'success': True, 'message': 'Vehicle access removed successfully'})
        except UserVehicle.DoesNotExist:
            return Response({'success': False, 'message': 'Vehicle access assignment not found'}, status=404)

class LocationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        imei = self.kwargs.get('imei')
        if imei:
            return Location.objects.filter(imei=imei)
        return Location.objects.none()
    
    @action(detail=False, methods=['get'])
    def latest(self, request, imei=None):
        latest = Location.objects.filter(imei=imei).order_by('-created_at').first()
        if not latest:
            return Response({'success': False, 'message': 'No location data found'}, status=404)
        
        serializer = self.get_serializer(latest)
        return Response({'success': True, 'data': serializer.data})
    
    @action(detail=False, methods=['get'])
    def range(self, request, imei=None):
        start_date = request.query_params.get('startDate')
        end_date = request.query_params.get('endDate')
        
        if not all([start_date, end_date]):
            return Response({'success': False, 'message': 'Start date and end date are required'}, status=400)
        
        locations = Location.objects.filter(
            imei=imei,
            created_at__range=[start_date, end_date]
        ).order_by('created_at')
        
        serializer = self.get_serializer(locations, many=True)
        return Response({'success': True, 'data': serializer.data})

    @action(detail=False, methods=['get'])
    def get_by_imei(self, request, imei=None):
        if not imei:
            return Response({'success': False, 'message': 'IMEI is required'}, status=400)
        
        locations = Location.objects.filter(imei=imei).order_by('created_at')
        serializer = self.get_serializer(locations, many=True)
        return Response({'success': True, 'data': serializer.data, 'message': 'Location history retrieved successfully'})

    @action(detail=False, methods=['get'])
    def combined(self, request, imei=None):
        start_date = request.query_params.get('startDate')
        end_date = request.query_params.get('endDate')
        
        if not all([start_date, end_date]):
            return Response({'success': False, 'message': 'Start date and end date are required'}, status=400)
        
        # Start date: 12:00:01 AM (beginning of day)
        start = datetime.strptime(start_date + 'T12:00:01', '%Y-%m-%dT%H:%M:%S')
        # End date: 11:59:59 PM (end of day)
        end = datetime.strptime(end_date + 'T23:59:59', '%Y-%m-%dT%H:%M:%S')
        
        # Get location data
        locations = Location.objects.filter(
            imei=imei,
            created_at__range=[start, end]
        ).order_by('created_at')
        
        # Get status data with ignition off
        statuses = Status.objects.filter(
            imei=imei,
            ignition=False,
            created_at__range=[start, end]
        ).order_by('created_at')
        
        # Combine and sort by created_at
        combined_data = []
        
        for loc in locations:
            combined_data.append({
                **self.get_serializer(loc).data,
                'type': 'location',
                'dataType': 'location'
            })
        
        for status in statuses:
            combined_data.append({
                **StatusSerializer(status).data,
                'type': 'status',
                'dataType': 'status'
            })
        
        # Sort by created_at
        combined_data.sort(key=lambda x: x['created_at'])
        
        return Response({'success': True, 'data': combined_data, 'message': 'Combined history data retrieved successfully'})

    @action(detail=False, methods=['get'])
    def report(self, request, imei=None):
        start_date = request.query_params.get('startDate')
        end_date = request.query_params.get('endDate')
        
        if not all([start_date, end_date]):
            return Response({'success': False, 'message': 'Start date and end date are required'}, status=400)
        
        # Validate date range (max 3 months)
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        three_months_ago = timezone.now() - timedelta(days=90)
        
        if start < three_months_ago:
            return Response({'success': False, 'message': 'Date range cannot exceed 3 months'}, status=400)
        
        # Get all location data for the date range
        locations = Location.objects.filter(
            imei=imei,
            created_at__range=[start, end]
        ).order_by('created_at')
        
        # Get all status data for the date range
        statuses = Status.objects.filter(
            imei=imei,
            created_at__range=[start, end]
        ).order_by('created_at')
        
        # Calculate statistics
        stats = self._calculate_report_stats(locations, statuses)
        
        # Generate daily data for charts
        daily_data = self._generate_daily_data(locations, start, end)
        
        report_data = {
            'stats': stats,
            'dailyData': daily_data,
            'rawData': {
                'locations': self.get_serializer(locations, many=True).data,
                'statuses': StatusSerializer(statuses, many=True).data
            }
        }
        
        return Response({'success': True, 'data': report_data, 'message': 'Report generated successfully'})

    def _calculate_report_stats(self, locations, statuses):
        if not locations:
            return {
                'totalKm': 0,
                'totalTime': 0,
                'averageSpeed': 0,
                'maxSpeed': 0,
                'totalIdleTime': 0,
                'totalRunningTime': 0,
                'totalOverspeedTime': 0,
                'totalStopTime': 0
            }
        
        # Calculate total distance
        total_km = 0
        for i in range(1, len(locations)):
            prev = locations[i-1]
            curr = locations[i]
            if prev.latitude and prev.longitude and curr.latitude and curr.longitude:
                distance = self._calculate_distance(
                    float(prev.latitude), float(prev.longitude),
                    float(curr.latitude), float(curr.longitude)
                )
                total_km += distance
        
        # Calculate time periods
        total_time = 0
        if len(locations) > 1:
            total_time = (locations[len(locations)-1].created_at - locations[0].created_at).total_seconds() / 60
        
        # Calculate speeds
        speeds = [loc.speed for loc in locations if loc.speed and loc.speed > 0]
        average_speed = sum(speeds) / len(speeds) if speeds else 0
        max_speed = max(speeds) if speeds else 0
        
        # Calculate time periods based on status
        total_idle_time = 0
        total_running_time = 0
        total_overspeed_time = 0
        total_stop_time = 0
        
        # Group statuses by day and calculate time periods
        status_by_day = {}
        for status in statuses:
            day = status.created_at.date().isoformat()
            if day not in status_by_day:
                status_by_day[day] = []
            status_by_day[day].append(status)
        
        # Calculate time periods for each day
        for day_statuses in status_by_day.values():
            day_statuses.sort(key=lambda x: x.created_at)
            
            for i in range(len(day_statuses) - 1):
                current = day_statuses[i]
                next_status = day_statuses[i + 1]
                duration = (next_status.created_at - current.created_at).total_seconds() / 60
                
                if current.ignition is False:
                    total_stop_time += duration
                elif current.ignition is True:
                    total_running_time += duration
        
        # Calculate idle time (when ignition is off but not moving)
        total_idle_time = total_stop_time
        
        # Calculate overspeed time (speed > 80 km/h)
        overspeed_locations = [loc for loc in locations if loc.speed and loc.speed > 80]
        if len(overspeed_locations) > 1:
            for i in range(1, len(overspeed_locations)):
                duration = (overspeed_locations[i].created_at - overspeed_locations[i-1].created_at).total_seconds() / 60
                total_overspeed_time += duration
        
        return {
            'totalKm': round(total_km, 2),
            'totalTime': round(total_time),
            'averageSpeed': round(average_speed, 1),
            'maxSpeed': round(max_speed),
            'totalIdleTime': round(total_idle_time),
            'totalRunningTime': round(total_running_time),
            'totalOverspeedTime': round(total_overspeed_time),
            'totalStopTime': round(total_stop_time)
        }

    def _generate_daily_data(self, locations, start_date, end_date):
        daily_data = {}
        current_date = start_date
        
        # Initialize daily data structure
        while current_date <= end_date:
            date_key = current_date.strftime('%Y-%m-%d')
            daily_data[date_key] = {
                'date': date_key,
                'averageSpeed': 0,
                'maxSpeed': 0,
                'totalKm': 0,
                'locationCount': 0
            }
            current_date += timedelta(days=1)
        
        # Group locations by day
        locations_by_day = {}
        for location in locations:
            date_key = location.created_at.strftime('%Y-%m-%d')
            if date_key not in locations_by_day:
                locations_by_day[date_key] = []
            locations_by_day[date_key].append(location)
        
        # Calculate daily statistics
        for date_key, day_locations in locations_by_day.items():
            if not day_locations:
                continue
            
            # Calculate speeds for the day
            speeds = [loc.speed for loc in day_locations if loc.speed and loc.speed > 0]
            average_speed = sum(speeds) / len(speeds) if speeds else 0
            max_speed = max(speeds) if speeds else 0
            
            # Calculate distance for the day
            total_km = 0
            for i in range(1, len(day_locations)):
                prev = day_locations[i-1]
                curr = day_locations[i]
                if prev.latitude and prev.longitude and curr.latitude and curr.longitude:
                    distance = self._calculate_distance(
                        float(prev.latitude), float(prev.longitude),
                        float(curr.latitude), float(curr.longitude)
                    )
                    total_km += distance
            
            daily_data[date_key] = {
                'date': date_key,
                'averageSpeed': round(average_speed, 1),
                'maxSpeed': round(max_speed),
                'totalKm': round(total_km, 2),
                'locationCount': len(day_locations)
            }
        
        return list(daily_data.values())

    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points using Haversine formula"""
        import math
        
        R = 6371  # Radius of the Earth in kilometers
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (
            math.sin(d_lat / 2) * math.sin(d_lat / 2) +
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
            math.sin(d_lon / 2) * math.sin(d_lon / 2)
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

class StatusViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Status.objects.all()
    serializer_class = StatusSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        imei = self.kwargs.get('imei')
        if imei:
            return Status.objects.filter(imei=imei)
        return Status.objects.none()
    
    @action(detail=False, methods=['get'])
    def latest(self, request, imei=None):
        latest = Status.objects.filter(imei=imei).order_by('-created_at').first()
        if not latest:
            return Response({'success': False, 'message': 'No status data found'}, status=404)
        
        serializer = self.get_serializer(latest)
        return Response({'success': True, 'data': serializer.data})

    @action(detail=False, methods=['get'])
    def get_by_imei(self, request, imei=None):
        if not imei:
            return Response({'success': False, 'message': 'IMEI is required'}, status=400)
        
        statuses = Status.objects.filter(imei=imei).order_by('created_at')
        serializer = self.get_serializer(statuses, many=True)
        return Response({'success': True, 'data': serializer.data, 'message': 'Status history retrieved successfully'})

    @action(detail=False, methods=['get'])
    def get_by_date_range(self, request, imei=None):
        if not imei:
            return Response({'success': False, 'message': 'IMEI is required'}, status=400)
        
        start_date = request.query_params.get('startDate')
        end_date = request.query_params.get('endDate')
        
        if not all([start_date, end_date]):
            return Response({'success': False, 'message': 'Start date and end date are required'}, status=400)
        
        statuses = Status.objects.filter(
            imei=imei,
            created_at__range=[start_date, end_date]
        ).order_by('created_at')
        
        serializer = self.get_serializer(statuses, many=True)
        return Response({'success': True, 'data': serializer.data, 'message': 'Status data retrieved successfully'})

class GeofenceViewSet(viewsets.ModelViewSet):
    queryset = Geofence.objects.all()
    serializer_class = GeofenceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role.name == 'Super Admin':
            return Geofence.objects.all()
        else:
            # Filter to only show geofences assigned to this user
            return Geofence.objects.filter(geofenceuser__user=user)

    @action(detail=False, methods=['get'])
    def get_by_imei(self, request, imei=None):
        if not imei:
            return Response({'success': False, 'message': 'IMEI is required'}, status=400)
        
        user = self.request.user
        
        if user.role.name == 'Super Admin':
            geofences = Geofence.objects.filter(
                vehicles__vehicle__imei=imei
            )
        else:
            # Filter to only show geofences assigned to this user
            geofences = Geofence.objects.filter(
                vehicles__vehicle__imei=imei,
                geofenceuser__user=user
            )
        
        serializer = self.get_serializer(geofences, many=True)
        return Response({'success': True, 'data': serializer.data, 'message': 'Geofences retrieved successfully'})

    def create(self, request, *args, **kwargs):
        user = request.user
        title = request.data.get('title')
        type = request.data.get('type')
        boundary = request.data.get('boundary')
        vehicle_ids = request.data.get('vehicleIds', [])
        user_ids = request.data.get('userIds', [])
        
        # Validate required fields
        if not all([title, type, boundary]):
            return Response({'success': False, 'message': 'Title, type, and boundary are required'}, status=400)
        
        # Validate boundary format
        if not isinstance(boundary, list) or len(boundary) < 3:
            return Response({'success': False, 'message': 'Boundary must have at least 3 points'}, status=400)
        
        # Create geofence
        geofence = Geofence.objects.create(
            title=title,
            type=type,
            boundary=boundary
        )
        
        # Assign to vehicles if provided
        if vehicle_ids:
            for vehicle_id in vehicle_ids:
                try:
                    vehicle = Vehicle.objects.get(id=vehicle_id)
                    GeofenceVehicle.objects.get_or_create(
                        geofence=geofence,
                        vehicle=vehicle
                    )
                except Vehicle.DoesNotExist:
                    continue
        
        # Always assign the current user to the geofence (creator)
        GeofenceUser.objects.get_or_create(
            geofence=geofence,
            user=user
        )
        
        # Assign to additional users if provided
        if user_ids:
            for user_id in user_ids:
                if user_id != user.id:
                    try:
                        target_user = User.objects.get(id=user_id)
                        GeofenceUser.objects.get_or_create(
                            geofence=geofence,
                            user=target_user
                        )
                    except User.DoesNotExist:
                        continue
        
        # Get updated geofence with assignments
        updated_geofence = Geofence.objects.get(id=geofence.id)
        serializer = self.get_serializer(updated_geofence)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Geofence created successfully'
        }, status=201)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        
        # Check access based on role
        if user.role.name != 'Super Admin':
            # Check if user has access to this geofence
            if not GeofenceUser.objects.filter(geofence=instance, user=user).exists():
                return Response({'success': False, 'message': 'Access denied to this geofence'}, status=403)
        
        # Update geofence
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Update vehicle assignments if provided
        vehicle_ids = request.data.get('vehicleIds')
        if vehicle_ids is not None:
            # Remove existing assignments
            GeofenceVehicle.objects.filter(geofence=instance).delete()
            
            # Create new assignments
            for vehicle_id in vehicle_ids:
                try:
                    vehicle = Vehicle.objects.get(id=vehicle_id)
                    GeofenceVehicle.objects.create(
                        geofence=instance,
                        vehicle=vehicle
                    )
                except Vehicle.DoesNotExist:
                    continue
        
        # Update user assignments if provided
        user_ids = request.data.get('userIds')
        if user_ids is not None:
            # Remove existing assignments
            GeofenceUser.objects.filter(geofence=instance).delete()
            
            # Always assign the current user
            GeofenceUser.objects.create(
                geofence=instance,
                user=user
            )
            
            # Create new assignments
            for user_id in user_ids:
                if user_id != user.id:
                    try:
                        target_user = User.objects.get(id=user_id)
                        GeofenceUser.objects.create(
                            geofence=instance,
                            user=target_user
                        )
                    except User.DoesNotExist:
                        continue
        
        # Get final updated geofence
        final_geofence = Geofence.objects.get(id=instance.id)
        final_serializer = self.get_serializer(final_geofence)
        
        return Response({
            'success': True,
            'data': final_serializer.data,
            'message': 'Geofence updated successfully'
        })

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role.name == 'Super Admin':
            return Notification.objects.all()
        else:
            # Return only notifications they have access to
            return Notification.objects.filter(usernotification__user=user)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        user = self.request.user
        count = UserNotification.objects.filter(
            user=user,
            is_read=False
        ).count()
        
        return Response({'success': True, 'data': {'count': count}})

    @action(detail=True, methods=['put'])
    def mark_as_read(self, request, pk=None):
        user = self.request.user
        notification_id = pk
        
        try:
            user_notification = UserNotification.objects.get(
                user=user,
                notification_id=notification_id
            )
            user_notification.is_read = True
            user_notification.save()
            
            return Response({'success': True, 'message': 'Notification marked as read'})
        except UserNotification.DoesNotExist:
            return Response({'success': False, 'message': 'Notification not found'}, status=404)

    def create(self, request, *args, **kwargs):
        # Only Super Admin can create notifications
        if request.user.role.name != 'Super Admin':
            return Response({
                'success': False,
                'message': 'Only Super Admin can create notifications'
            }, status=403)
        
        title = request.data.get('title')
        message = request.data.get('message')
        type = request.data.get('type')
        target_user_ids = request.data.get('targetUserIds', [])
        target_role_ids = request.data.get('targetRoleIds', [])
        
        # Validate required fields
        if not all([title, message, type]):
            return Response({
                'success': False,
                'message': 'Title, message, and type are required'
            }, status=400)
        
        # Validate type
        if type not in ['all', 'specific', 'role']:
            return Response({
                'success': False,
                'message': 'Type must be all, specific, or role'
            }, status=400)
        
        # Validate targetUserIds for specific type
        if type == 'specific' and not target_user_ids:
            return Response({
                'success': False,
                'message': 'targetUserIds array is required for specific type'
            }, status=400)
        
        # Validate targetRoleIds for role type
        if type == 'role' and not target_role_ids:
            return Response({
                'success': False,
                'message': 'targetRoleIds array is required for role type'
            }, status=400)
        
        # Create notification
        notification = Notification.objects.create(
            title=title,
            message=message,
            type=type,
            sent_by=request.user
        )
        
        # Create user-notification relations based on type
        if type == 'all':
            # Get all active users
            all_users = User.objects.filter(status='ACTIVE')
            for user in all_users:
                UserNotification.objects.create(
                    user=user,
                    notification=notification
                )
        elif type == 'specific' and target_user_ids:
            # Create user-notification relations for specific users
            for user_id in target_user_ids:
                try:
                    user = User.objects.get(id=user_id, status='ACTIVE')
                    UserNotification.objects.create(
                        user=user,
                        notification=notification
                    )
                except User.DoesNotExist:
                    continue
        elif type == 'role' and target_role_ids:
            # Get users with specific roles
            users_with_roles = User.objects.filter(
                role_id__in=target_role_ids,
                status='ACTIVE'
            )
            for user in users_with_roles:
                UserNotification.objects.create(
                    user=user,
                    notification=notification
                )
        
        # TODO: Send push notifications via Firebase
        # For now, just return success
        
        return Response({
            'success': True,
            'message': 'Notification created successfully',
            'data': self.get_serializer(notification).data
        }, status=201)

class PopupViewSet(viewsets.ModelViewSet):
    queryset = Popup.objects.all()
    serializer_class = PopupSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.action == 'list' and not self.request.user.is_staff:
            return Popup.objects.filter(is_active=True)
        return Popup.objects.all()
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active popups (public endpoint)"""
        popups = Popup.objects.filter(is_active=True).order_by('-created_at')
        serializer = self.get_serializer(popups, many=True)
        
        # Add full image URLs to popups
        popups_with_images = []
        for popup in serializer.data:
            popup_data = dict(popup)
            if popup_data.get('image'):
                popup_data['imageUrl'] = f"http://84.247.131.246:7070/uploads/popups/{popup_data['image']}"
            else:
                popup_data['imageUrl'] = None
            popups_with_images.append(popup_data)
        
        return Response({
            'success': True,
            'data': popups_with_images,
            'message': 'Active popups retrieved successfully'
        })

    def create(self, request, *args, **kwargs):
        # Only Super Admin can create popups
        if request.user.role.name != 'Super Admin':
            return Response({
                'success': False,
                'message': 'Access denied. Only Super Admin can create popups'
            }, status=403)
        
        popup_data = {
            'title': request.data.get('title'),
            'message': request.data.get('message'),
            'is_active': request.data.get('isActive', True)
        }
        
        # Handle image upload
        if 'image' in request.FILES:
            popup_data['image'] = request.FILES['image']
        
        serializer = self.get_serializer(data=popup_data)
        serializer.is_valid(raise_exception=True)
        popup = serializer.save()
        
        # Add full image URL
        popup_with_image = dict(serializer.data)
        if popup_with_image.get('image'):
            popup_with_image['imageUrl'] = f"http://84.247.131.246:7070/uploads/popups/{popup_with_image['image']}"
        else:
            popup_with_image['imageUrl'] = None
        
        return Response({
            'success': True,
            'data': popup_with_image,
            'message': 'Popup created successfully'
        }, status=201)

    def update(self, request, *args, **kwargs):
        # Only Super Admin can update popups
        if request.user.role.name != 'Super Admin':
            return Response({
                'success': False,
                'message': 'Access denied. Only Super Admin can update popups'
            }, status=403)
        
        instance = self.get_object()
        update_data = {
            'title': request.data.get('title'),
            'message': request.data.get('message')
        }
        
        # Handle isActive field
        if 'isActive' in request.data:
            update_data['is_active'] = request.data['isActive']
        
        # Handle image update
        if 'image' in request.FILES:
            # Delete old image if exists
            if instance.image:
                import os
                old_image_path = os.path.join('uploads', 'popups', str(instance.image))
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            update_data['image'] = request.FILES['image']
        
        serializer = self.get_serializer(instance, data=update_data, partial=True)
        serializer.is_valid(raise_exception=True)
        popup = serializer.save()
        
        # Add full image URL
        popup_with_image = dict(serializer.data)
        if popup_with_image.get('image'):
            popup_with_image['imageUrl'] = f"http://84.247.131.246:7070/uploads/popups/{popup_with_image['image']}"
        else:
            popup_with_image['imageUrl'] = None
        
        return Response({
            'success': True,
            'data': popup_with_image,
            'message': 'Popup updated successfully'
        })

    def destroy(self, request, *args, **kwargs):
        # Only Super Admin can delete popups
        if request.user.role.name != 'Super Admin':
            return Response({
                'success': False,
                'message': 'Access denied. Only Super Admin can delete popups'
            }, status=403)
        
        instance = self.get_object()
        
        # Delete associated image
        if instance.image:
            import os
            image_path = os.path.join('uploads', 'popups', str(instance.image))
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except OSError:
                    pass  # Continue with popup deletion even if image deletion fails
        
        instance.delete()
        return Response({
            'success': True,
            'data': {'success': True},
            'message': 'Popup deleted successfully'
        })

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if not self.request.user.is_staff:
            return User.objects.none()
        return User.objects.all()
    
    @action(detail=False, methods=['get'])
    def by_phone(self, request):
        phone = request.query_params.get('phone')
        if not phone:
            return Response({'success': False, 'message': 'Phone number is required'}, status=400)
        
        try:
            user = User.objects.get(phone=phone)
            serializer = self.get_serializer(user)
            return Response({'success': True, 'data': serializer.data})
        except User.DoesNotExist:
            return Response({'success': False, 'message': 'User not found'}, status=404)

    @action(detail=False, methods=['put'])
    def update_fcm_token(self, request):
        phone = request.data.get('phone')
        fcm_token = request.data.get('fcmToken')
        
        if not phone or not fcm_token:
            return Response({'success': False, 'message': 'Phone number and FCM token are required'}, status=400)
        
        try:
            user = User.objects.get(phone=phone)
            user.fcm_token = fcm_token
            user.save()
            
            return Response({
                'success': True,
                'data': {'fcmToken': user.fcm_token},
                'message': 'FCM token updated successfully'
            })
        except User.DoesNotExist:
            return Response({'success': False, 'message': 'User not found'}, status=404)

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def permissions(self, request):
        permissions = Permission.objects.all()
        serializer = PermissionSerializer(permissions, many=True)
        return Response({'success': True, 'data': serializer.data, 'message': 'Permissions retrieved successfully'})
    
    @action(detail=True, methods=['put'])
    def update_permissions(self, request, pk=None):
        role_id = pk
        permission_ids = request.data.get('permissionIds', [])
        
        try:
            role = Role.objects.get(id=role_id)
            
            # Remove existing permissions
            RolePermission.objects.filter(role=role).delete()
            
            # Add new permissions
            for permission_id in permission_ids:
                try:
                    permission = Permission.objects.get(id=permission_id)
                    RolePermission.objects.create(role=role, permission=permission)
                except Permission.DoesNotExist:
                    continue
            
            # Get updated role
            updated_role = Role.objects.get(id=role_id)
            serializer = self.get_serializer(updated_role)
            return Response({'success': True, 'data': serializer.data, 'message': 'Role permissions updated successfully'})
        except Role.DoesNotExist:
            return Response({'success': False, 'message': 'Role not found'}, status=404)

class RelayViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def turn_relay_on(self, request):
        imei = request.data.get('imei')
        if not imei:
            return Response({'success': False, 'message': 'IMEI is required'}, status=400)
        
        # Check if user has access to this vehicle
        user = self.request.user
        try:
            user_vehicle = UserVehicle.objects.get(
                user=user,
                vehicle__imei=imei
            )
        except UserVehicle.DoesNotExist:
            return Response({'success': False, 'message': 'Vehicle not found or access denied'}, status=404)
        
        # TODO: Implement actual relay control logic
        # For now, just return success
        return Response({
            'success': True,
            'data': {
                'relayStatus': 'ON',
                'command': 'HFYD#',
                'message': 'Relay turned ON successfully',
                'deviceConfirmed': True
            }
        })
    
    @action(detail=False, methods=['post'])
    def turn_relay_off(self, request):
        imei = request.data.get('imei')
        if not imei:
            return Response({'success': False, 'message': 'IMEI is required'}, status=400)
        
        # Check if user has access to this vehicle
        user = self.request.user
        try:
            user_vehicle = UserVehicle.objects.get(
                user=user,
                vehicle__imei=imei
            )
        except UserVehicle.DoesNotExist:
            return Response({'success': False, 'message': 'Vehicle not found or access denied'}, status=404)
        
        # TODO: Implement actual relay control logic
        # For now, just return success
        return Response({
            'success': True,
            'data': {
                'relayStatus': 'OFF',
                'command': 'DYD#',
                'message': 'Relay turned OFF successfully',
                'deviceConfirmed': True
            }
        })
    
    @action(detail=False, methods=['get'])
    def get_relay_status(self, request, imei=None):
        if not imei:
            return Response({'success': False, 'message': 'IMEI is required'}, status=400)
        
        # Check if user has access to this vehicle
        user = self.request.user
        try:
            user_vehicle = UserVehicle.objects.get(
                user=user,
                vehicle__imei=imei
            )
        except UserVehicle.DoesNotExist:
            return Response({'success': False, 'message': 'Vehicle not found or access denied'}, status=404)
        
        # Get latest status
        try:
            latest_status = Status.objects.filter(imei=imei).latest('created_at')
            relay_status = 'ON' if latest_status.relay else 'OFF'
        except Status.DoesNotExist:
            relay_status = 'OFF'
        
        return Response({
            'success': True,
            'data': {
                'relayStatus': relay_status,
                'lastUpdated': latest_status.created_at if 'latest_status' in locals() else None
            }
        })
    
    @action(detail=False, methods=['get'])
    def debug_connections(self, request):
        # TODO: Implement actual connection debugging
        # For now, return mock data
        return Response({
            'success': True,
            'data': {
                'totalConnections': 0,
                'deviceCount': 0,
                'connectedDevices': []
            }
        })