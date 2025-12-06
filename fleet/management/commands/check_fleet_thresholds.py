from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from datetime import datetime, timedelta
import logging

from fleet.models import Vehicle, VehicleServicing, VehicleDocument, UserVehicle
from core.models import User
from shared.models import Notification, UserNotification
from api_common.services.nodejs_notification_service import send_push_notification_via_nodejs

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check fleet management thresholds (servicing and document renewal) and send mobile app notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--servicing-only',
            action='store_true',
            help='Only check servicing thresholds',
        )
        parser.add_argument(
            '--documents-only',
            action='store_true',
            help='Only check document renewal thresholds',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending notifications',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        servicing_only = options['servicing_only']
        documents_only = options['documents_only']
        dry_run = options['dry_run']
        verbose = options['verbose']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE: No notifications will be sent'))

        # Get or create a system user for sending notifications
        system_user = self._get_system_user()

        servicing_count = 0
        document_count = 0
        notifications_sent = 0

        try:
            if not documents_only:
                servicing_count, servicing_notifications = self._check_servicing_thresholds(
                    system_user, dry_run, verbose
                )
                notifications_sent += servicing_notifications

            if not servicing_only:
                document_count, document_notifications = self._check_document_thresholds(
                    system_user, dry_run, verbose
                )
                notifications_sent += document_notifications

            # Summary
            self.stdout.write(self.style.SUCCESS('\n=== Summary ==='))
            if not documents_only:
                self.stdout.write(f'Servicing checks: {servicing_count} vehicle(s) need servicing')
            if not servicing_only:
                self.stdout.write(f'Document checks: {document_count} document(s) need renewal')
            self.stdout.write(f'Total notifications sent: {notifications_sent}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error checking thresholds: {e}'))
            logger.error(f'Error in check_fleet_thresholds: {e}', exc_info=True)
            raise

    def _get_system_user(self):
        """Get or create a system user for sending notifications"""
        try:
            # Try to get a Super Admin user
            super_admin = User.objects.filter(
                groups__name='Super Admin',
                is_active=True
            ).first()
            if super_admin:
                return super_admin

            # If no Super Admin, get any active user
            user = User.objects.filter(is_active=True).first()
            if user:
                return user

            # Last resort: create a system user (shouldn't happen in production)
            self.stdout.write(self.style.WARNING('No active users found, creating system user'))
            return User.objects.create(
                username='system',
                phone='system',
                name='System',
                is_active=True
            )
        except Exception as e:
            logger.error(f'Error getting system user: {e}')
            raise

    def _check_servicing_thresholds(self, system_user, dry_run, verbose):
        """Check servicing thresholds for all vehicles"""
        vehicles_needing_servicing = []
        notifications_sent = 0

        # Get all vehicles
        vehicles = Vehicle.objects.filter(is_active=True).select_related('device')

        for vehicle in vehicles:
            try:
                # Get last servicing record
                last_servicing = VehicleServicing.objects.filter(
                    vehicle=vehicle
                ).order_by('-date', '-odometer').first()

                # Skip vehicle if no previous servicing record exists
                if not last_servicing:
                    if verbose:
                        self.stdout.write(
                            f'Skipping vehicle {vehicle.name} ({vehicle.imei}) - no previous service record'
                        )
                    continue

                # Calculate threshold: last_service_odometer + (servicing_distance_period * 0.90)
                # 90% complete means 10% remaining
                threshold_odometer = float(last_servicing.odometer) + (
                    float(vehicle.servicing_distance_period) * 0.90
                )
                needs_servicing = float(vehicle.odometer) >= threshold_odometer

                if needs_servicing:
                    vehicles_needing_servicing.append({
                        'vehicle': vehicle,
                        'current_odometer': float(vehicle.odometer),
                        'threshold_odometer': threshold_odometer,
                        'last_servicing': last_servicing,
                    })

                    if verbose:
                        self.stdout.write(
                            f'Vehicle {vehicle.name} ({vehicle.imei}) needs servicing: '
                            f'Current: {vehicle.odometer} km, Threshold: {threshold_odometer:.2f} km'
                        )

            except Exception as e:
                logger.error(f'Error checking servicing for vehicle {vehicle.imei}: {e}')
                if verbose:
                    self.stdout.write(
                        self.style.ERROR(f'Error checking vehicle {vehicle.imei}: {e}')
                    )

        # Send notifications for vehicles needing servicing
        for vehicle_info in vehicles_needing_servicing:
            vehicle = vehicle_info['vehicle']
            try:
                # Get users who should receive notification
                target_users = self._get_vehicle_notification_users(vehicle)

                if not target_users:
                    if verbose:
                        self.stdout.write(
                            f'No users to notify for vehicle {vehicle.name} ({vehicle.imei})'
                        )
                    continue

                # Create entity identifier for duplicate checking (use IMEI as unique identifier)
                entity_identifier = vehicle.imei

                # Check if notification was sent for this vehicle in last 24 hours
                if not self._should_send_notification_for_entity(vehicle.id, 'servicing', entity_identifier):
                    if verbose:
                        self.stdout.write(
                            f'Skipping notification for vehicle {vehicle.name} ({vehicle.imei}) - already sent in last 24 hours'
                        )
                    continue

                # Create notification message
                last_service_info = ''
                if vehicle_info['last_servicing']:
                    last_service_info = (
                        f'Last service: {vehicle_info["last_servicing"].date} '
                        f'at {vehicle_info["last_servicing"].odometer} km. '
                    )
                else:
                    last_service_info = 'No previous service record. '

                # Include vehicle number in title and message for better entity identification
                title = f'Vehicle Servicing Required: {vehicle.name} ({vehicle.vehicleNo})'
                message = (
                    f'{vehicle.name} ({vehicle.vehicleNo}) - IMEI: {vehicle.imei} needs servicing. '
                    f'{last_service_info}'
                    f'Current odometer: {vehicle_info["current_odometer"]:.0f} km. '
                    f'Threshold: {vehicle_info["threshold_odometer"]:.0f} km.'
                )

                if not dry_run:
                    notifications_sent += self._send_notification(
                        system_user,
                        target_users,
                        title,
                        message,
                        'servicing',
                        vehicle.id
                    )
                else:
                    if verbose:
                        self.stdout.write(
                            f'[DRY RUN] Would send notification to {len(target_users)} user(s): {title}'
                        )
                    notifications_sent += len(target_users)

            except Exception as e:
                logger.error(f'Error sending notification for vehicle {vehicle.imei}: {e}')
                if verbose:
                    self.stdout.write(
                        self.style.ERROR(f'Error sending notification for {vehicle.imei}: {e}')
                    )

        return len(vehicles_needing_servicing), notifications_sent

    def _check_document_thresholds(self, system_user, dry_run, verbose):
        """Check document renewal thresholds for all documents"""
        documents_needing_renewal = []
        notifications_sent = 0

        # Get all documents
        documents = VehicleDocument.objects.filter(
            vehicle__is_active=True
        ).select_related('vehicle')

        current_date = datetime.now().date()

        for document in documents:
            try:
                # Calculate actual expiry date: last_expire_date + expire_in_month months
                expiry_year = document.last_expire_date.year
                expiry_month = document.last_expire_date.month + document.expire_in_month
                expiry_day = document.last_expire_date.day

                # Handle year overflow
                while expiry_month > 12:
                    expiry_month -= 12
                    expiry_year += 1

                expiry_date = datetime(expiry_year, expiry_month, expiry_day).date()

                # Calculate threshold: 1 week before expiry
                threshold_date = expiry_date - timedelta(days=7)
                
                # Check if needs notification (1 week before expiry OR already expired)
                needs_renewal = current_date >= threshold_date

                if needs_renewal:
                    documents_needing_renewal.append({
                        'document': document,
                        'expiry_date': expiry_date,
                        'threshold_date': threshold_date,
                        'current_date': current_date,
                    })

                    if verbose:
                        self.stdout.write(
                            f'Document {document.title} for {document.vehicle.name} needs renewal: '
                            f'Expiry: {expiry_date}, Threshold (1 week before): {threshold_date}, Current: {current_date}'
                        )

            except Exception as e:
                logger.error(f'Error checking document {document.id}: {e}')
                if verbose:
                    self.stdout.write(
                        self.style.ERROR(f'Error checking document {document.id}: {e}')
                    )

        # Send notifications for documents needing renewal
        for doc_info in documents_needing_renewal:
            document = doc_info['document']
            vehicle = document.vehicle
            try:
                # Get users who should receive notification
                target_users = self._get_vehicle_notification_users(vehicle)

                if not target_users:
                    if verbose:
                        self.stdout.write(
                            f'No users to notify for document {document.title} of {vehicle.name}'
                        )
                    continue

                # Create entity identifier for duplicate checking (document title + vehicle IMEI)
                entity_identifier = f'{document.title} {vehicle.imei}'

                # Check if notification was sent for this document in last 24 hours
                if not self._should_send_notification_for_entity(document.id, 'document', entity_identifier):
                    if verbose:
                        self.stdout.write(
                            f'Skipping notification for document {document.title} ({vehicle.imei}) - already sent in last 24 hours'
                        )
                    continue

                # Get expiry date from doc_info (already calculated)
                expiry_date = doc_info['expiry_date']
                current_date = doc_info['current_date']
                
                # Calculate days until expiry
                days_until_expiry = (expiry_date - current_date).days
                
                # Create notification message based on expiry status
                # Include document title and vehicle number for better entity identification
                title = f'Document Renewal Required: {document.title} ({vehicle.vehicleNo})'
                
                if days_until_expiry > 0:
                    # Not expired yet - show days remaining
                    message = (
                        f'{document.title} for {vehicle.name} ({vehicle.vehicleNo}) - IMEI: {vehicle.imei} expires in {days_until_expiry} days. '
                        f'Last expire date: {document.last_expire_date}. Please renew soon.'
                    )
                else:
                    # Already expired - show urgent message
                    expired_days = abs(days_until_expiry)
                    message = (
                        f'{document.title} for {vehicle.name} ({vehicle.vehicleNo}) - IMEI: {vehicle.imei} has EXPIRED - renew as soon as possible. '
                        f'Last expire date: {document.last_expire_date}. '
                        f'Expired {expired_days} day{"s" if expired_days != 1 else ""} ago.'
                    )

                if not dry_run:
                    notifications_sent += self._send_notification(
                        system_user,
                        target_users,
                        title,
                        message,
                        'document',
                        document.id
                    )
                else:
                    if verbose:
                        self.stdout.write(
                            f'[DRY RUN] Would send notification to {len(target_users)} user(s): {title}'
                        )
                    notifications_sent += len(target_users)

            except Exception as e:
                logger.error(f'Error sending notification for document {document.id}: {e}')
                if verbose:
                    self.stdout.write(
                        self.style.ERROR(f'Error sending notification for document {document.id}: {e}')
                    )

        return len(documents_needing_renewal), notifications_sent

    def _get_vehicle_notification_users(self, vehicle):
        """Get all users who should receive notifications for a vehicle"""
        users = set()

        # Get Super Admin users
        super_admins = User.objects.filter(
            groups__name='Super Admin',
            is_active=True,
            fcm_token__isnull=False
        ).exclude(fcm_token='')
        users.update(super_admins)

        # Get users with isMain=True for this vehicle and notification=True
        main_users = User.objects.filter(
            userVehicles__vehicle=vehicle,
            userVehicles__isMain=True,
            userVehicles__notification=True,
            is_active=True,
            fcm_token__isnull=False
        ).exclude(fcm_token='')
        users.update(main_users)

        return list(users)

    def _should_send_notification_for_entity(self, entity_id, entity_type, entity_identifier):
        """
        Check if notification was sent for this specific entity in last 24 hours
        Prevents duplicate notifications for the same vehicle/document
        
        Args:
            entity_id: ID of the entity (vehicle_id or document_id)
            entity_type: 'servicing' or 'document'
            entity_identifier: Unique identifier string (vehicle IMEI/name or document title + vehicle)
        
        Returns:
            bool: True if notification should be sent (no recent duplicate), False otherwise
        """
        yesterday = timezone.now() - timedelta(hours=24)
        
        if entity_type == 'servicing':
            # Check for notifications with vehicle identifier in message
            recent_notifications = Notification.objects.filter(
                title__icontains='Vehicle Servicing Required',
                message__icontains=entity_identifier,
                createdAt__gte=yesterday
            ).exists()
        else:  # document
            # Check for notifications with document identifier in message
            recent_notifications = Notification.objects.filter(
                title__icontains='Document Renewal Required',
                message__icontains=entity_identifier,
                createdAt__gte=yesterday
            ).exists()
        
        # Return True if no recent notification found (should send), False if duplicate exists
        return not recent_notifications

    def _send_notification(self, system_user, target_users, title, message, entity_type, entity_id):
        """Create notification and send push notification"""
        notifications_created = 0

        try:
            with transaction.atomic():
                # Create notification record
                notification = Notification.objects.create(
                    title=title,
                    message=message,
                    type='specific',
                    sentBy=system_user
                )

                # Create UserNotification records
                user_ids = []
                for user in target_users:
                    UserNotification.objects.create(
                        notification=notification,
                        user=user,
                        isRead=False
                    )
                    user_ids.append(user.id)
                    notifications_created += 1

                # Send push notification via Node.js
                try:
                    send_push_notification_via_nodejs(
                        notification_id=notification.id,
                        title=title,
                        message=message,
                        target_user_ids=user_ids
                    )
                    logger.info(f'Sent {notifications_created} notifications for {entity_type} {entity_id}')
                except Exception as nodejs_error:
                    logger.error(f'Node.js notification error: {nodejs_error}')
                    # Don't fail if Node.js fails, notification is still saved

        except Exception as e:
            logger.error(f'Error creating notification: {e}')
            raise

        return notifications_created

