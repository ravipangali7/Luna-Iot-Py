"""
Django management command to manage user wallet balances interactively

Usage:
    python manage.py manage_wallet
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from decimal import Decimal, InvalidOperation
from core.models import User
from finance.models import Wallet


class Command(BaseCommand):
    help = 'Interactively manage user wallet balances (add or subtract amounts)'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== Wallet Management Tool ===\n')
        )
        
        try:
            # Step 1: Ask for operation (add/subtract)
            operation = self._get_operation()
            
            # Step 2: Ask for amount
            amount = self._get_amount()
            
            # Step 3: Ask for target (all/phone)
            target_type = self._get_target_type()
            
            # Step 4: Process based on target type
            if target_type == 'all':
                self._process_all_users(operation, amount)
            else:  # phone
                phone_numbers = self._get_phone_numbers()
                self._process_phone_numbers(phone_numbers, operation, amount)
            
            self.stdout.write(
                self.style.SUCCESS('\n=== Operation completed successfully! ===')
            )
            
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\n\nOperation cancelled by user.')
            )
        except Exception as e:
            raise CommandError(f'Error during wallet management: {str(e)}')

    def _get_operation(self):
        """Get operation type (add or subtract)"""
        while True:
            operation = input('\nSelect operation (add/subtract): ').strip().lower()
            if operation in ['add', 'subtract']:
                return operation
            self.stdout.write(
                self.style.ERROR('Invalid option. Please enter "add" or "subtract".')
            )

    def _get_amount(self):
        """Get amount to add/subtract"""
        while True:
            try:
                amount_str = input('\nEnter amount: ').strip()
                amount = Decimal(amount_str)
                if amount <= 0:
                    self.stdout.write(
                        self.style.ERROR('Amount must be greater than 0.')
                    )
                    continue
                return amount
            except (InvalidOperation, ValueError):
                self.stdout.write(
                    self.style.ERROR('Invalid amount. Please enter a valid number.')
                )

    def _get_target_type(self):
        """Get target type (all or phone)"""
        while True:
            target = input('\nSelect target (all/phone): ').strip().lower()
            if target in ['all', 'phone']:
                return target
            self.stdout.write(
                self.style.ERROR('Invalid option. Please enter "all" or "phone".')
            )

    def _get_phone_numbers(self):
        """Get phone numbers from user input"""
        while True:
            phone_input = input('\nEnter phone number(s) (comma-separated or single): ').strip()
            if not phone_input:
                self.stdout.write(
                    self.style.ERROR('Phone number cannot be empty.')
                )
                continue
            
            # Parse phone numbers (split by comma and strip whitespace)
            phone_numbers = [phone.strip() for phone in phone_input.split(',') if phone.strip()]
            
            if not phone_numbers:
                self.stdout.write(
                    self.style.ERROR('No valid phone numbers found.')
                )
                continue
            
            return phone_numbers

    def _process_all_users(self, operation, amount):
        """Process all users with wallets"""
        self.stdout.write(
            self.style.SUCCESS(f'\nProcessing {operation} operation for all users...')
        )
        
        # Get all users
        all_users = User.objects.all()
        total_users = all_users.count()
        
        self.stdout.write(f'Found {total_users} users in the system.')
        
        success_count = 0
        skipped_count = 0
        error_count = 0
        created_wallets = 0
        
        for user in all_users:
            try:
                # Get or create wallet
                wallet, created = Wallet.objects.get_or_create(
                    user=user,
                    defaults={'balance': Decimal('0.00')}
                )
                
                if created:
                    created_wallets += 1
                    self.stdout.write(
                        f'  Created wallet for user {user.name or user.phone} (ID: {user.id})'
                    )
                
                # Perform operation
                result = self._perform_operation(wallet, operation, amount, user)
                
                if result['success']:
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ {operation.capitalize()}ed {amount} to wallet for '
                            f'{user.name or user.phone} (ID: {user.id}). '
                            f'New balance: {wallet.balance}'
                        )
                    )
                elif result['skipped']:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠ Skipped {user.name or user.phone} (ID: {user.id}): '
                            f'{result["message"]}'
                        )
                    )
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'  ✗ Error processing {user.name or user.phone} (ID: {user.id}): '
                            f'{result["message"]}'
                        )
                    )
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'  ✗ Error processing user {user.id}: {str(e)}'
                    )
                )
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\n=== Summary ===\n'
                f'Total users processed: {total_users}\n'
                f'Successful operations: {success_count}\n'
                f'Skipped: {skipped_count}\n'
                f'Errors: {error_count}\n'
                f'Wallets created: {created_wallets}'
            )
        )

    def _process_phone_numbers(self, phone_numbers, operation, amount):
        """Process specific phone numbers"""
        self.stdout.write(
            self.style.SUCCESS(
                f'\nProcessing {operation} operation for {len(phone_numbers)} phone number(s)...'
            )
        )
        
        success_count = 0
        skipped_count = 0
        error_count = 0
        not_found_count = 0
        created_wallets = 0
        
        for phone in phone_numbers:
            try:
                # Find user by phone
                try:
                    user = User.objects.get(phone=phone)
                except User.DoesNotExist:
                    not_found_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠ User with phone number "{phone}" not found. Skipping.'
                        )
                    )
                    continue
                
                # Get or create wallet
                wallet, created = Wallet.objects.get_or_create(
                    user=user,
                    defaults={'balance': Decimal('0.00')}
                )
                
                if created:
                    created_wallets += 1
                    self.stdout.write(
                        f'  Created wallet for user {user.name or user.phone} (ID: {user.id})'
                    )
                
                # Perform operation
                result = self._perform_operation(wallet, operation, amount, user)
                
                if result['success']:
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ {operation.capitalize()}ed {amount} to wallet for '
                            f'{user.name or user.phone} (Phone: {phone}). '
                            f'New balance: {wallet.balance}'
                        )
                    )
                elif result['skipped']:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠ Skipped {user.name or user.phone} (Phone: {phone}): '
                            f'{result["message"]}'
                        )
                    )
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'  ✗ Error processing {user.name or user.phone} (Phone: {phone}): '
                            f'{result["message"]}'
                        )
                    )
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'  ✗ Error processing phone "{phone}": {str(e)}'
                    )
                )
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\n=== Summary ===\n'
                f'Phone numbers processed: {len(phone_numbers)}\n'
                f'Successful operations: {success_count}\n'
                f'Users not found: {not_found_count}\n'
                f'Skipped: {skipped_count}\n'
                f'Errors: {error_count}\n'
                f'Wallets created: {created_wallets}'
            )
        )

    def _perform_operation(self, wallet, operation, amount, user):
        """Perform add or subtract operation on wallet"""
        try:
            with transaction.atomic():
                if operation == 'add':
                    success = wallet.add_balance(
                        amount,
                        description=f"Balance {operation}ed via manage_wallet command",
                        performed_by=None
                    )
                    if success:
                        return {'success': True, 'skipped': False, 'message': ''}
                    else:
                        return {
                            'success': False,
                            'skipped': False,
                            'message': 'Failed to add balance'
                        }
                else:  # subtract
                    # Check balance before subtracting
                    if wallet.balance < amount:
                        return {
                            'success': False,
                            'skipped': True,
                            'message': f'Insufficient balance. Current: {wallet.balance}, Required: {amount}'
                        }
                    
                    success = wallet.subtract_balance(
                        amount,
                        description=f"Balance {operation}ed via manage_wallet command",
                        performed_by=None
                    )
                    if success:
                        return {'success': True, 'skipped': False, 'message': ''}
                    else:
                        return {
                            'success': False,
                            'skipped': False,
                            'message': 'Failed to subtract balance'
                        }
        except Exception as e:
            return {
                'success': False,
                'skipped': False,
                'message': str(e)
            }

