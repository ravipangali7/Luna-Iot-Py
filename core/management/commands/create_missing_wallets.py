"""
Django management command to create wallets for users who don't have one
Usage: python manage.py create_missing_wallets
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core.models import User, Wallet


class Command(BaseCommand):
    help = 'Create wallets with 0 balance for users who don\'t have one'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually creating wallets',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of wallets to create in each batch (default: 100)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        
        self.stdout.write(
            self.style.SUCCESS('Starting wallet creation process...')
        )
        
        try:
            # Find users without wallets
            users_without_wallets = User.objects.filter(wallet__isnull=True)
            total_users = users_without_wallets.count()
            
            if total_users == 0:
                self.stdout.write(
                    self.style.SUCCESS('All users already have wallets!')
                )
                return
            
            self.stdout.write(
                self.style.WARNING(f'Found {total_users} users without wallets')
            )
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING('DRY RUN MODE - No wallets will be created')
                )
                self._show_users_preview(users_without_wallets[:10])
                if total_users > 10:
                    self.stdout.write(f'... and {total_users - 10} more users')
                return
            
            # Create wallets in batches
            created_count = 0
            failed_count = 0
            
            for i in range(0, total_users, batch_size):
                batch_users = users_without_wallets[i:i + batch_size]
                batch_created, batch_failed = self._create_wallets_batch(batch_users)
                created_count += batch_created
                failed_count += batch_failed
                
                self.stdout.write(
                    f'Processed batch {i//batch_size + 1}: '
                    f'{batch_created} wallets created, {batch_failed} failed'
                )
            
            # Final summary
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nWallet creation completed!\n'
                    f'Total wallets created: {created_count}\n'
                    f'Total failures: {failed_count}\n'
                    f'Total users processed: {total_users}'
                )
            )
            
            if failed_count > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f'Warning: {failed_count} wallets could not be created. '
                        'Check the logs above for details.'
                    )
                )
                
        except Exception as e:
            raise CommandError(f'Error during wallet creation: {str(e)}')

    def _show_users_preview(self, users):
        """Show a preview of users who would get wallets"""
        self.stdout.write('\nUsers who would get wallets:')
        self.stdout.write('-' * 50)
        for user in users:
            self.stdout.write(f'ID: {user.id}, Name: {user.name}, Phone: {user.phone}')

    def _create_wallets_batch(self, users):
        """Create wallets for a batch of users"""
        created_count = 0
        failed_count = 0
        
        for user in users:
            try:
                with transaction.atomic():
                    wallet = Wallet.objects.create(
                        user=user,
                        balance=0.00
                    )
                    created_count += 1
                    self.stdout.write(
                        f'  ✓ Created wallet for user {user.name} (ID: {user.id})'
                    )
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'  ✗ Failed to create wallet for user {user.name} (ID: {user.id}): {str(e)}'
                    )
                )
        
        return created_count, failed_count
