from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = 'Grants standard permissions to the Teacher group'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("🛠  Starting Permission Fix..."))

        # 1. Get Teacher Group
        teacher_group, created = Group.objects.get_or_create(name='Teacher')
        
        # 2. List of Apps Teachers Need Access To
        # Add every app name that appears in your 'school_system' folder
        apps_to_grant = [
            'attendance', 'exam', 'lms', 'student_info', 'timetable', 
            'staff', 'library', 'workload', 'admission', 'dashboard'
        ]

        total_granted = 0

        for app_label in apps_to_grant:
            try:
                # Get Content Types for the App
                content_types = ContentType.objects.filter(app_label=app_label)
                
                if not content_types.exists():
                    self.stdout.write(f"   ⚠️  Skipping '{app_label}': No models found.")
                    continue

                # Get Permissions (View, Add, Change)
                permissions = Permission.objects.filter(
                    content_type__in=content_types,
                    codename__regex=r'^(view_|add_|change_)' 
                )
                
                if permissions.exists():
                    teacher_group.permissions.add(*permissions)
                    count = permissions.count()
                    total_granted += count
                    self.stdout.write(f"   ✅ {app_label}: Granted {count} permissions.")
                else:
                    self.stdout.write(f"   ℹ️  {app_label}: No permissions available.")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ Error on {app_label}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"\n🚀 DONE: Added {total_granted} permissions to 'Teacher' group."))
        self.stdout.write("👉 NOW: Log out and Log back in as Anjali to see the changes.")