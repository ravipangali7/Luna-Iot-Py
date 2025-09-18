from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import User


class Command(BaseCommand):
    help = 'Set up default groups and permissions for the IOT system'

    def handle(self, *args, **options):
        self.stdout.write('Setting up groups and permissions...')
        
        # Create groups
        super_admin_group, created = Group.objects.get_or_create(name='Super Admin')
        dealer_group, created = Group.objects.get_or_create(name='Dealer')
        customer_group, created = Group.objects.get_or_create(name='Customer')
        
        if created:
            self.stdout.write(f'Created group: {super_admin_group.name}')
        else:
            self.stdout.write(f'Group already exists: {super_admin_group.name}')
        
        # Define permissions for each group (only include permissions that exist)
        group_permissions = {
            'Super Admin': [
                # User permissions
                'add_user', 'change_user', 'delete_user', 'view_user',
                # Basic permissions that should exist
                'view_permission', 'add_permission', 'change_permission', 'delete_permission',
                'view_group', 'add_group', 'change_group', 'delete_group'
            ],
            'Dealer': [
                # User permissions
                'view_user',
                # Basic permissions
                'view_permission', 'view_group'
            ],
            'Customer': [
                # User permissions
                'view_user'
            ]
        }
        
        # Assign permissions to groups
        for group_name, permission_codenames in group_permissions.items():
            group = Group.objects.get(name=group_name)
            
            # Clear existing permissions
            group.permissions.clear()
            
            # Add new permissions
            for codename in permission_codenames:
                try:
                    # Try to find permission by codename
                    permission = Permission.objects.get(codename=codename)
                    group.permissions.add(permission)
                    self.stdout.write(f'Added permission {codename} to {group_name}')
                except Permission.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'Permission {codename} not found, skipping...')
                    )
        
        # Create a super admin user if it doesn't exist
        if not User.objects.filter(phone='977').exists():
            admin_user = User.objects.create_user(
                username='977',
                phone='977',
                name='Super Admin',
                password='admin123'
            )
            admin_user.groups.add(super_admin_group)
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()
            self.stdout.write('Created super admin user: 977/admin123')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up groups and permissions!')
        )