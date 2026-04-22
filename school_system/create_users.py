import os
import django

# 1. Setup Django Environment
# This allows the script to read your settings and database
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

# 2. Your Logic Starts Here
from django.contrib.auth.models import User, Group

def run():
    print("🚀 Starting user setup...")

    # --- Create Groups ---
    admin_group, _ = Group.objects.get_or_create(name='Admin')
    teacher_group, _ = Group.objects.get_or_create(name='Teacher')
    student_group, _ = Group.objects.get_or_create(name='Student')
    print("✅ Groups Ready: Admin, Teacher, Student")

    # --- Create Admin Test User ---
    # We use get_or_create so it doesn't crash if you run it twice
    u_admin, created = User.objects.get_or_create(username='admin')
    u_admin.set_password('123')
    u_admin.is_staff = True # Optional: lets them access Django Admin panel
    u_admin.save()
    u_admin.groups.add(admin_group)
    if created:
        print(f"👤 Created Admin User: {u_admin.username}")
    else:
        print(f"🔄 Updated Admin User: {u_admin.username}")

    # --- Create Teacher Test User ---
    u_teacher, created = User.objects.get_or_create(username='teacher')
    u_teacher.set_password('123')
    u_teacher.save()
    u_teacher.groups.add(teacher_group)
    if created:
        print(f"👤 Created Teacher User: {u_teacher.username}")
    else:
        print(f"🔄 Updated Teacher User: {u_teacher.username}")

    # --- Create Student Test User ---
    u_student, created = User.objects.get_or_create(username='student')
    u_student.set_password('123')
    u_student.save()
    u_student.groups.add(student_group)
    if created:
        print(f"👤 Created Student User: {u_student.username}")
    else:
        print(f"🔄 Updated Student User: {u_student.username}")

    print("\n✨ Done! Login with password: 123")

if __name__ == '__main__':
    run()