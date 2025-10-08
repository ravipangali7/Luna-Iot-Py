from django.core.management.base import BaseCommand
from device.models import SubscriptionPlan, Device


class Command(BaseCommand):
    help = 'Set default subscription plan (Bronze) for all devices that don\'t have a subscription plan'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without actually updating',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Update all devices, even those that already have a subscription plan',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        try:
            # Find the Bronze subscription plan
            try:
                bronze_plan = SubscriptionPlan.objects.get(title__icontains='bronze')
                self.stdout.write(f'Found Bronze subscription plan: {bronze_plan.title} (ID: {bronze_plan.id}) - Rs {bronze_plan.price}')
            except SubscriptionPlan.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR('Bronze subscription plan not found! Please create a subscription plan with "Bronze" in the title.')
                )
                return
            except SubscriptionPlan.MultipleObjectsReturned:
                bronze_plans = SubscriptionPlan.objects.filter(title__icontains='bronze')
                self.stdout.write(
                    self.style.WARNING(f'Multiple Bronze plans found: {[plan.title for plan in bronze_plans]}')
                )
                bronze_plan = bronze_plans.first()
                self.stdout.write(f'Using first one: {bronze_plan.title} (ID: {bronze_plan.id})')
            
            # Get devices to update
            if force:
                devices_to_update = Device.objects.all()
                self.stdout.write(f'Force mode: Will update ALL {devices_to_update.count()} devices')
            else:
                devices_to_update = Device.objects.filter(subscription_plan__isnull=True)
                self.stdout.write(f'Found {devices_to_update.count()} devices without subscription plans')
            
            if devices_to_update.count() == 0:
                self.stdout.write(self.style.SUCCESS('No devices need to be updated.'))
                return
            
            updated_count = 0
            
            for device in devices_to_update:
                current_plan = device.subscription_plan
                if current_plan:
                    self.stdout.write(f'Device {device.imei}: Currently has {current_plan.title} - Rs {current_plan.price}')
                else:
                    self.stdout.write(f'Device {device.imei}: No subscription plan')
                
                if not dry_run:
                    device.subscription_plan = bronze_plan
                    device.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Updated device {device.imei} to Bronze plan')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Would update device {device.imei} to Bronze plan')
                    )
            
            if not dry_run:
                self.stdout.write(
                    self.style.SUCCESS(f'\nSuccessfully updated {updated_count} devices to Bronze subscription plan!')
                )
                self.stdout.write(f'All devices now have subscription plan: {bronze_plan.title} - Rs {bronze_plan.price}')
            else:
                self.stdout.write(
                    self.style.WARNING(f'\nDry run completed. Would update {devices_to_update.count()} devices to Bronze plan.')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {e}')
            )
            import traceback
            traceback.print_exc()
