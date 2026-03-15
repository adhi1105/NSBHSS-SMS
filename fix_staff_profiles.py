import os
import django
import sys

# 1. Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from django.contrib.auth.models import User
from staff.models import Staff, Department

def fix_missing_profiles():
    print("--------------------------------------------------")
    print("🔍 Checking for teachers without Staff Profiles...")
    print("--------------------------------------------------")

    # 2. Ensure a default Department exists
    dept, _ = Department.objects.get_or_create(name="General")

    # 3. Find Users who are Staff but have NO profile
    users_without_profile = User.objects.filter(is_staff=True).exclude(staff__isnull=False)
    
    count = users_without_profile.count()

    if count == 0:
        print("🎉 Good news! All teachers already have profiles.")
        return

    print(f"⚠️  Found {count} teachers missing profiles. Fixing now...\n")

    # 4. Create the missing profiles
    fixed_count = 0
    for user in users_without_profile:
        try:
            # Generate a unique ID (using 'staff_id' instead of 'employee_id')
            new_id = f"TCH-{user.id:03d}" 
            
            Staff.objects.create(
                user=user,
                department=dept,
                designation="Teacher",
                status="active",
                is_teaching_staff=True,
                staff_id=new_id  # <--- CHANGED THIS FIELD NAME
            )
            print(f"   ✅ Fixed: {user.username} (ID: {new_id})")
            fixed_count += 1
        except Exception as e:
            print(f"   ❌ Error fixing {user.username}: {e}")

    print("\n--------------------------------------------------")
    print(f"🚀 SUCCESS: Created {fixed_count} Staff Profiles.")
    print("--------------------------------------------------")

if __name__ == '__main__':
    fix_missing_profiles()