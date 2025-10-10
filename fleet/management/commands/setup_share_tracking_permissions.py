from django.core.management.base import BaseCommand
from core.models import User
from fleet.models.vehicle import Vehicle
from fleet.models.user_vehicle import UserVehicle


class Command(BaseCommand):
    help = 'Setup share tracking permissions for users'

    def add_arguments(self, parser):
        parser.add_argument('--user-phone', type=str, help='User phone number')
        parser.add_argument('--imei', type=str, help='Vehicle IMEI')
        parser.add_argument('--enable', action='store_true', help='Enable share tracking permission')
        parser.add_argument('--disable', action='store_true', help='Disable share tracking permission')
        parser.add_argument('--list', action='store_true', help='List current permissions')

    def handle(self, *args, **options):
        if options['list']:
            self.list_permissions()
        elif options['user_phone'] and options['imei']:
            self.update_permission(
                options['user_phone'], 
                options['imei'], 
                options['enable'], 
                options['disable']
            )
        else:
            self.stdout.write(
                self.style.ERROR('Please provide --user-phone and --imei, or use --list')
            )

    def list_permissions(self):
        """List all user vehicle permissions"""
        self.stdout.write(self.style.SUCCESS('Current User Vehicle Permissions:'))
        self.stdout.write('-' * 80)
        
        user_vehicles = UserVehicle.objects.select_related('user', 'vehicle').all()
        
        for uv in user_vehicles:
            self.stdout.write(
                f"User: {uv.user.name} ({uv.user.phone}) | "
                f"Vehicle: {uv.vehicle.name} ({uv.vehicle.imei}) | "
                f"Share Tracking: {uv.shareTracking} | "
                f"All Access: {uv.allAccess}"
            )

    def update_permission(self, user_phone, imei, enable, disable):
        """Update share tracking permission for a user-vehicle pair"""
        try:
            user = User.objects.get(phone=user_phone)
            vehicle = Vehicle.objects.get(imei=imei)
            
            user_vehicle, created = UserVehicle.objects.get_or_create(
                user=user,
                vehicle=vehicle,
                defaults={'shareTracking': enable}
            )
            
            if not created:
                if enable:
                    user_vehicle.shareTracking = True
                    user_vehicle.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Enabled share tracking for {user.name} on {vehicle.name}'
                        )
                    )
                elif disable:
                    user_vehicle.shareTracking = False
                    user_vehicle.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Disabled share tracking for {user.name} on {vehicle.name}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Current share tracking permission for {user.name} on {vehicle.name}: {user_vehicle.shareTracking}'
                        )
                    )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created new user-vehicle relationship for {user.name} on {vehicle.name}'
                    )
                )
                
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with phone {user_phone} not found')
            )
        except Vehicle.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Vehicle with IMEI {imei} not found')
            )
