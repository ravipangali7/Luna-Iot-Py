from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.db.models import Count
from core.models import User


class Command(BaseCommand):
    help = 'Find users without groups and assign them to Customer group by default'

    def handle(self, *args, **options):
        self.stdout.write('Finding users without groups...')
        
        # Find users without any groups
        users_without_groups = User.objects.annotate(
            group_count=Count('groups')
        ).filter(group_count=0)
        
        user_count = users_without_groups.count()
        
        if user_count == 0:
            self.stdout.write(
                self.style.SUCCESS('No users without groups found. All users already have roles assigned.')
            )
            return
        
        # Display list of users without groups
        self.stdout.write(f'\nFound {user_count} user(s) without groups:')
        self.stdout.write('-' * 60)
        for user in users_without_groups:
            user_name = user.name or 'N/A'
            user_phone = user.phone or 'N/A'
            self.stdout.write(f'  ID: {user.id} | Name: {user_name} | Phone: {user_phone}')
        self.stdout.write('-' * 60)
        
        # Get or create Customer group
        try:
            customer_group = Group.objects.get(name='Customer')
        except Group.DoesNotExist:
            self.stdout.write(
                self.style.WARNING('Customer group does not exist. Creating it...')
            )
            customer_group = Group.objects.create(name='Customer')
            self.stdout.write('Customer group created.')
        
        # Assign users to Customer group
        self.stdout.write(f'\nAssigning {user_count} user(s) to Customer group...')
        assigned_count = 0
        
        for user in users_without_groups:
            user.groups.add(customer_group)
            assigned_count += 1
            user_name = user.name or user.phone
            self.stdout.write(f'  ✓ Assigned {user_name} (ID: {user.id}) to Customer group')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully assigned {assigned_count} user(s) to Customer group!'
            )
        )

