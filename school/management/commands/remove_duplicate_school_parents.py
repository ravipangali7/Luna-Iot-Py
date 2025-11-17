"""
Django management command to remove duplicate SchoolParent entries
where the same parent has the same bus and same child_name assigned multiple times.

Usage:
    python manage.py remove_duplicate_school_parents
    python manage.py remove_duplicate_school_parents --dry-run
    python manage.py remove_duplicate_school_parents --keep-newest
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from collections import defaultdict
from school.models import SchoolParent


class Command(BaseCommand):
    help = 'Remove duplicate SchoolParent entries where the same parent has the same bus and same child_name assigned multiple times'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be removed without actually deleting duplicates',
        )
        parser.add_argument(
            '--keep-newest',
            action='store_true',
            help='Keep the newest entry instead of the oldest (default: keep oldest)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        keep_newest = options['keep_newest']
        
        self.stdout.write(
            self.style.SUCCESS('Starting duplicate SchoolParent removal process...')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No records will be deleted')
            )
        
        try:
            # Get all SchoolParent entries with their buses
            all_parents = SchoolParent.objects.select_related('parent').prefetch_related('school_buses').all()
            
            # Helper function to normalize child_name (treat empty/null as same value)
            def normalize_child_name(child_name):
                return (child_name or '').strip().lower() if child_name else ''
            
            # Group by (parent_id, bus_id, child_name) combination
            # Key: (parent_id, bus_id, normalized_child_name), Value: list of SchoolParent IDs
            duplicates_map = defaultdict(list)
            
            self.stdout.write('Analyzing SchoolParent entries...')
            
            for school_parent in all_parents:
                parent_id = school_parent.parent.id
                # Normalize child_name for grouping
                child_name_normalized = normalize_child_name(school_parent.child_name)
                
                # Check each bus assigned to this parent
                for school_bus in school_parent.school_buses.all():
                    # Key includes parent_id, bus_id, and normalized child_name
                    key = (parent_id, school_bus.id, child_name_normalized)
                    bus_name = f"{school_bus.bus.name} ({school_bus.bus.vehicleNo})" if school_bus.bus else f'SchoolBus ID {school_bus.id}'
                    duplicates_map[key].append({
                        'id': school_parent.id,
                        'parent_name': school_parent.parent.name or school_parent.parent.phone,
                        'bus_name': bus_name,
                        'created_at': school_parent.created_at,
                        'child_name': school_parent.child_name
                    })
            
            # Find duplicates (entries with more than one SchoolParent for same parent+bus+child_name)
            duplicates_to_remove = []
            duplicates_to_keep = []
            
            for (parent_id, bus_id, child_name_norm), entries in duplicates_map.items():
                if len(entries) > 1:
                    # Sort by created_at
                    entries_sorted = sorted(entries, key=lambda x: x['created_at'], reverse=keep_newest)
                    
                    # Keep the first one (oldest if keep_newest=False, newest if keep_newest=True)
                    keep_entry = entries_sorted[0]
                    remove_entries = entries_sorted[1:]
                    
                    duplicates_to_keep.append(keep_entry)
                    duplicates_to_remove.extend(remove_entries)
            
            # Display results
            total_duplicates = len(duplicates_to_remove)
            unique_duplicate_groups = len([k for k, v in duplicates_map.items() if len(v) > 1])
            
            if total_duplicates == 0:
                self.stdout.write(
                    self.style.SUCCESS('\n✓ No duplicate SchoolParent entries found!')
                )
                return
            
            self.stdout.write('\n' + '=' * 80)
            self.stdout.write(self.style.SUCCESS('DUPLICATE ANALYSIS RESULTS'))
            self.stdout.write('=' * 80)
            self.stdout.write(f'Total duplicate groups found: {unique_duplicate_groups}')
            self.stdout.write(f'Total duplicate entries to remove: {total_duplicates}')
            self.stdout.write(f'Total entries to keep: {len(duplicates_to_keep)}')
            self.stdout.write('')
            
            # Show details by group
            self.stdout.write(self.style.WARNING('Duplicate Groups:'))
            self.stdout.write('-' * 80)
            
            for (parent_id, bus_id, child_name_norm), entries in duplicates_map.items():
                if len(entries) > 1:
                    entries_sorted = sorted(entries, key=lambda x: x['created_at'], reverse=keep_newest)
                    keep_entry = entries_sorted[0]
                    remove_entries = entries_sorted[1:]
                    
                    parent_name = entries[0]['parent_name']
                    bus_name = entries[0]['bus_name']
                    child_display = entries[0]['child_name'] if entries[0]['child_name'] else '(no child name)'
                    
                    self.stdout.write(f'\nParent: {parent_name} (ID: {parent_id}) | Bus: {bus_name} (ID: {bus_id}) | Child: {child_display}')
                    self.stdout.write(f'  ✓ KEEP: SchoolParent ID {keep_entry["id"]} (Created: {keep_entry["created_at"]})')
                    if keep_entry['child_name']:
                        self.stdout.write(f'      Child Name: {keep_entry["child_name"]}')
                    
                    for remove_entry in remove_entries:
                        self.stdout.write(f'  ✗ REMOVE: SchoolParent ID {remove_entry["id"]} (Created: {remove_entry["created_at"]})')
                        if remove_entry['child_name']:
                            self.stdout.write(f'      Child Name: {remove_entry["child_name"]}')
            
            if dry_run:
                self.stdout.write('\n' + '=' * 80)
                self.stdout.write(
                    self.style.WARNING(
                        f'\nDRY RUN COMPLETE\n'
                        f'Would remove {total_duplicates} duplicate SchoolParent entries.\n'
                        f'Run without --dry-run to actually delete these duplicates.'
                    )
                )
                return
            
            # Confirm deletion
            self.stdout.write('\n' + '=' * 80)
            self.stdout.write(
                self.style.WARNING(
                    f'About to delete {total_duplicates} duplicate SchoolParent entries...'
                )
            )
            
            # Perform deletion
            deleted_count = 0
            failed_count = 0
            
            with transaction.atomic():
                for entry in duplicates_to_remove:
                    try:
                        school_parent = SchoolParent.objects.get(id=entry['id'])
                        parent_name = entry['parent_name']
                        school_parent.delete()
                        deleted_count += 1
                        self.stdout.write(
                            f'  ✓ Deleted SchoolParent ID {entry["id"]} (Parent: {parent_name})'
                        )
                    except SchoolParent.DoesNotExist:
                        failed_count += 1
                        self.stdout.write(
                            self.style.ERROR(
                                f'  ✗ SchoolParent ID {entry["id"]} not found (may have been already deleted)'
                            )
                        )
                    except Exception as e:
                        failed_count += 1
                        self.stdout.write(
                            self.style.ERROR(
                                f'  ✗ Failed to delete SchoolParent ID {entry["id"]}: {str(e)}'
                            )
                        )
            
            # Final summary
            self.stdout.write('\n' + '=' * 80)
            self.stdout.write(self.style.SUCCESS('DUPLICATE REMOVAL COMPLETED'))
            self.stdout.write('=' * 80)
            self.stdout.write(f'Total duplicates found: {total_duplicates}')
            self.stdout.write(f'Successfully deleted: {deleted_count}')
            self.stdout.write(f'Failed to delete: {failed_count}')
            self.stdout.write(f'Entries kept: {len(duplicates_to_keep)}')
            
            if failed_count > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f'\nWarning: {failed_count} entries could not be deleted. '
                        'Check the logs above for details.'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n✓ Successfully removed all {deleted_count} duplicate entries!'
                    )
                )
                
        except Exception as e:
            raise CommandError(f'Error during duplicate removal: {str(e)}')

