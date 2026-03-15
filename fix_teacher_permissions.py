import os
import django

# 1. Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

def fix_permissions():
    print("--------------------------------------------------")
    print("🛠  Fixing Teacher Permissions for Modules...")
    print("--------------------------------------------------")

    # 2. Get or Create the Teacher Group
    teacher_group, created = Group.objects.get_or_create(name='Teacher')
    if created:
        print("   ✅ Created 'Teacher' group.")
    else:
        print("   ℹ️  Found existing 'Teacher' group.")

    # 3. List of Apps Teachers NEED access to
    # Add any other apps here (e.g., 'library', 'transportation') if needed
    apps_to_grant = [
        'attendance', 
        'exam', 
        'lms', 
        'student_info', 
        'timetable', 
        'staff',       # To view their own profile
        'library',     # If they manage books
        'workload'     # To view their schedule
    ]

    count = 0
    
    # 4. Loop through apps and grant permissions
    for app_label in apps_to_grant:
        try:
            # Find all content types (models) for this app
            content_types = ContentType.objects.filter(app_label=app_label)
            
            # Find permissions linked to these models
            # We grant: view, add, change (but usually NOT delete)
            permissions = Permission.objects.filter(
                content_type__in=content_types,
                codename__regex=r'^(view_|add_|change_)' 
            )

            if permissions.exists():
                teacher_group.permissions.add(*permissions)
                print(f"   ✅ Granted {permissions.count()} permissions for '{app_label}'")
                count += permissions.count()
            else:
                print(f"   ⚠️  No permissions found for app '{app_label}' (Check app name)")

        except Exception as e:
            print(f"   ❌ Error processing {app_label}: {e}")

    print("--------------------------------------------------")
    print(f"🚀 SUCCESS: Added {count} permissions to the Teacher group.")
    print("   Teachers like Anjali can now access these modules.")
    print("--------------------------------------------------")

if __name__ == '__main__':
    fix_permissions()