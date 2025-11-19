"""
Django management command to generate due transactions for expired vehicles and institutional modules

Usage:
    python manage.py generate_due_transactions
    python manage.py generate_due_transactions --dry-run
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from finance.models import DueTransaction, DueTransactionParticular
from fleet.models import Vehicle, UserVehicle
from core.models import InstituteModule, Module, MySetting
from school.models import SchoolParent


class Command(BaseCommand):
    help = 'Generate due transactions for expired vehicles (individual) and expired institutional modules (school)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating due transactions',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(
            self.style.SUCCESS('Starting due transaction generation process...')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No due transactions will be created')
            )
        
        try:
            # Get MySetting for pricing
            try:
                my_setting = MySetting.objects.first()
                if not my_setting:
                    self.stdout.write(
                        self.style.WARNING('MySetting not found. Using default values.')
                    )
                    parent_price = Decimal('0.00')
                else:
                    parent_price = my_setting.parent_price or Decimal('0.00')
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Error getting MySetting: {str(e)}. Using default values.')
                )
                parent_price = Decimal('0.00')
            
            # Part 1: Individual (Vehicles)
            self.stdout.write(self.style.SUCCESS('\n=== Processing Individual Vehicles ==='))
            individual_count = self.process_individual_vehicles(dry_run)
            
            # Part 2: Institutional (School Module)
            self.stdout.write(self.style.SUCCESS('\n=== Processing Institutional (School Module) ==='))
            institutional_count = self.process_institutional_modules(dry_run, parent_price)
            
            # Summary
            self.stdout.write(self.style.SUCCESS('\n=== Summary ==='))
            self.stdout.write(f'Individual due transactions processed: {individual_count}')
            self.stdout.write(f'Institutional due transactions processed: {institutional_count}')
            self.stdout.write(
                self.style.SUCCESS('\nDue transaction generation completed successfully!')
            )
        
        except Exception as e:
            raise CommandError(f'Error generating due transactions: {str(e)}')

    def process_individual_vehicles(self, dry_run):
        """Process individual vehicles with expired dates"""
        count = 0
        now = timezone.now()
        
        # Get all vehicles with expired expireDate
        expired_vehicles = Vehicle.objects.filter(
            expireDate__lt=now,
            expireDate__isnull=False
        ).select_related('device', 'device__subscription_plan').prefetch_related('userVehicles')
        
        self.stdout.write(f'Found {expired_vehicles.count()} expired vehicles')
        
        for vehicle in expired_vehicles:
            try:
                # Get main user (UserVehicle with isMain=True)
                main_user_vehicle = vehicle.userVehicles.filter(isMain=True).first()
                
                if not main_user_vehicle:
                    self.stdout.write(
                        self.style.WARNING(f'  Vehicle {vehicle.id} ({vehicle.name}) has no main user. Skipping.')
                    )
                    continue
                
                main_user = main_user_vehicle.user
                
                # Check if unpaid due transaction already exists for this specific vehicle
                vehicle_particular_exists = DueTransactionParticular.objects.filter(
                    vehicle=vehicle,
                    due_transaction__is_paid=False
                ).exists()
                
                if vehicle_particular_exists:
                    self.stdout.write(
                        self.style.WARNING(f'  Vehicle {vehicle.id} already has an unpaid due transaction. Skipping.')
                    )
                    continue
                
                # Check if main_user is a Dealer
                is_dealer = main_user.groups.filter(name='Dealer').exists()
                
                # Calculate price from device subscription plan
                customer_price = Decimal('0.00')
                dealer_price = None
                
                if vehicle.device and vehicle.device.subscription_plan:
                    subscription_plan = vehicle.device.subscription_plan
                    customer_price = Decimal(str(subscription_plan.price))
                    # Get dealer price if available, fallback to customer price
                    if subscription_plan.dealer_price:
                        dealer_price = Decimal(str(subscription_plan.dealer_price))
                    else:
                        dealer_price = customer_price  # Fallback to customer price if dealer_price is null
                else:
                    # Fallback: use default from MySetting or zero
                    try:
                        my_setting = MySetting.objects.first()
                        if my_setting and hasattr(my_setting, 'vehicle_price'):
                            customer_price = Decimal(str(my_setting.vehicle_price)) if my_setting.vehicle_price else Decimal('0.00')
                            dealer_price = customer_price  # Use same price if no subscription plan
                        else:
                            customer_price = Decimal('0.00')
                            dealer_price = Decimal('0.00')
                    except:
                        customer_price = Decimal('0.00')
                        dealer_price = Decimal('0.00')
                    
                    if customer_price == Decimal('0.00'):
                        self.stdout.write(
                            self.style.WARNING(
                                f'  Vehicle {vehicle.id} has no subscription plan and no default price. Using 0.00.'
                            )
                        )
                
                # Use customer_price for transaction totals (backward compatibility)
                vehicle_price = customer_price
                
                if dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  [DRY RUN] Would create/update due transaction for Vehicle {vehicle.id} '
                            f'({vehicle.name}) - User {main_user.id} ({main_user.name or main_user.phone})'
                        )
                    )
                    count += 1
                    continue
                
                # Create new due transaction per vehicle
                with transaction.atomic():
                    # Calculate renew_date (one year before expire_date)
                    renew_date = vehicle.expireDate - timedelta(days=365)
                    if renew_date > now:
                        renew_date = now
                    
                    # Calculate VAT and total before creating
                    try:
                        my_setting = MySetting.objects.first()
                        vat_percent = Decimal(str(my_setting.vat_percent)) if my_setting and my_setting.vat_percent else Decimal('0.00')
                    except:
                        vat_percent = Decimal('0.00')
                    
                    vat_amount = (vehicle_price * vat_percent) / Decimal('100')
                    total_amount = vehicle_price + vat_amount
                    
                    # Create new due transaction for this vehicle
                    new_due = DueTransaction.objects.create(
                        user=main_user,
                        subtotal=vehicle_price,
                        vat=vat_amount,
                        total=total_amount,
                        renew_date=renew_date,
                        expire_date=vehicle.expireDate
                    )
                    
                    # Create particular linked to vehicle
                    # Store both customer price (amount) and dealer price (dealer_amount)
                    DueTransactionParticular.objects.create(
                        due_transaction=new_due,
                        particular=f"Vehicle {vehicle.id} - {vehicle.name} ({vehicle.vehicleNo}) - Renewal",
                        type='vehicle',
                        vehicle=vehicle,  # Link to vehicle
                        amount=customer_price,  # Always store customer price
                        dealer_amount=dealer_price if dealer_price else None,  # Store dealer price if available
                        quantity=1
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  Created new due transaction {new_due.id} for Vehicle {vehicle.id} ({vehicle.name}) - User {main_user.id}'
                        )
                    )
                    
                    count += 1
            
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  Error processing vehicle {vehicle.id}: {str(e)}')
                )
                continue
        
        return count

    def process_institutional_modules(self, dry_run, parent_price):
        """Process institutional modules (school) with expired dates"""
        count = 0
        now = timezone.now()
        
        try:
            # Get school module
            school_module = Module.objects.get(slug='school')
        except Module.DoesNotExist:
            self.stdout.write(
                self.style.WARNING('School module not found. Skipping institutional processing.')
            )
            return 0
        
        # Get all InstituteModule with school module and expired expire_date
        expired_institute_modules = InstituteModule.objects.filter(
            module=school_module,
            expire_date__lt=now,
            expire_date__isnull=False
        ).select_related('institute', 'module').prefetch_related('users')
        
        self.stdout.write(f'Found {expired_institute_modules.count()} expired school institute modules')
        
        for institute_module in expired_institute_modules:
            try:
                # Get first user from institute_module.users
                first_user = institute_module.users.first()
                
                if not first_user:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  InstituteModule {institute_module.id} ({institute_module.institute.name}) '
                            f'has no users. Skipping.'
                        )
                    )
                    continue
                
                # Get all SchoolParent related to this institute
                school_parents = SchoolParent.objects.filter(
                    school_buses__institute=institute_module.institute
                ).select_related('parent').distinct()
                
                if not school_parents.exists():
                    self.stdout.write(
                        self.style.WARNING(
                            f'  InstituteModule {institute_module.id} has no school parents. Skipping.'
                        )
                    )
                    continue
                
                # Check if unpaid DueTransaction exists for this user
                unpaid_due = DueTransaction.objects.filter(
                    user=first_user,
                    is_paid=False
                ).first()
                
                # Check which parents already have particulars in unpaid due
                existing_parent_ids = set()
                if unpaid_due:
                    existing_particulars = DueTransactionParticular.objects.filter(
                        due_transaction=unpaid_due,
                        type='parent',
                        institute=institute_module.institute
                    )
                    # Extract parent IDs from particular descriptions
                    for part in existing_particulars:
                        # Assuming format: "Parent {parent_id} - {name}"
                        try:
                            # Try to extract parent ID from particular text
                            # This is a simple approach - can be enhanced
                            if 'Parent' in part.particular:
                                # Extract ID if possible, otherwise skip
                                pass
                        except:
                            pass
                
                # Calculate renewal price
                renewal_price = institute_module.renewal_price or parent_price
                
                if dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  [DRY RUN] Would create/update due transaction for InstituteModule {institute_module.id} '
                            f'({institute_module.institute.name}) - User {first_user.id} '
                            f'({first_user.name or first_user.phone}) - {school_parents.count()} parents'
                        )
                    )
                    count += 1
                    continue
                
                # Create or update due transaction
                with transaction.atomic():
                    if unpaid_due:
                        # Add particulars for parents that don't exist yet
                        added_count = 0
                        for school_parent in school_parents:
                            # Check if particular for this parent already exists
                            parent_particular_exists = DueTransactionParticular.objects.filter(
                                due_transaction=unpaid_due,
                                type='parent',
                                institute=institute_module.institute,
                                particular__icontains=f"Parent {school_parent.parent.id}"
                            ).exists()
                            
                            if not parent_particular_exists:
                                DueTransactionParticular.objects.create(
                                    due_transaction=unpaid_due,
                                    particular=f"Parent {school_parent.parent.id} - {school_parent.parent.name or school_parent.parent.phone} - {institute_module.institute.name}",
                                    type='parent',
                                    institute=institute_module.institute,
                                    amount=renewal_price,
                                    quantity=1
                                )
                                added_count += 1
                        
                        if added_count > 0:
                            # Recalculate totals
                            unpaid_due.subtotal = sum(
                                Decimal(str(p.total)) for p in unpaid_due.particulars.all()
                            )
                            unpaid_due.calculate_totals()
                            unpaid_due.save()
                            
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  Added {added_count} particulars for InstituteModule {institute_module.id} '
                                    f'to existing due transaction {unpaid_due.id}'
                                )
                            )
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'  All parents for InstituteModule {institute_module.id} already have particulars. Skipping.'
                                )
                            )
                    else:
                        # Create new due transaction
                        # Calculate renew_date (one year before expire_date)
                        renew_date = institute_module.expire_date - timedelta(days=365)
                        if renew_date > now:
                            renew_date = now
                        
                        # Calculate total subtotal
                        total_subtotal = renewal_price * school_parents.count()
                        
                        # Calculate VAT and total before creating
                        try:
                            my_setting = MySetting.objects.first()
                            vat_percent = Decimal(str(my_setting.vat_percent)) if my_setting and my_setting.vat_percent else Decimal('0.00')
                        except:
                            vat_percent = Decimal('0.00')
                        
                        # Ensure total_subtotal is Decimal
                        total_subtotal = Decimal(str(total_subtotal))
                        vat_amount = (total_subtotal * vat_percent) / Decimal('100')
                        total_amount = total_subtotal + vat_amount
                        
                        new_due = DueTransaction.objects.create(
                            user=first_user,
                            subtotal=total_subtotal,
                            vat=vat_amount,
                            total=total_amount,
                            renew_date=renew_date,
                            expire_date=institute_module.expire_date
                        )
                        
                        # Create particulars for all parents
                        for school_parent in school_parents:
                            DueTransactionParticular.objects.create(
                                due_transaction=new_due,
                                particular=f"Parent {school_parent.parent.id} - {school_parent.parent.name or school_parent.parent.phone} - {institute_module.institute.name}",
                                type='parent',
                                institute=institute_module.institute,
                                amount=renewal_price,
                                quantity=1
                            )
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  Created new due transaction {new_due.id} for InstituteModule {institute_module.id} '
                                f'({institute_module.institute.name}) - User {first_user.id} - {school_parents.count()} parents'
                            )
                        )
                    
                    count += 1
            
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  Error processing InstituteModule {institute_module.id}: {str(e)}')
                )
                continue
        
        return count

