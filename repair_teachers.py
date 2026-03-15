from django.contrib.auth.models import User, Group
from school_system.models import Subject
from staff.models import Staff, Department
from django.utils import timezone
import random

def repair_data():
    subjects_list = [
        ('Mathematics', 'MATH'), ('Physics', 'PHY'), ('Chemistry', 'CHEM'),
        ('Biology', 'BIO'), ('Computer Science', 'CS'), ('English Literature', 'ENG'),
        ('History', 'HIST'), ('Geography', 'GEO'), ('Economics', 'ECO'),
        ('Physical Education', 'PE')
    ]

    staff_group, _ = Group.objects.get_or_create(name='Staff')
    print("--- STARTING REPAIR ---")

    for name, code in subjects_list:
        # 1. Ensure Department Exists
        dept_obj, _ = Department.objects.get_or_create(name=name)

        # 2. Get or Create User
        username = f"teacher_{code.lower()}"
        email = f"{username}@school.com"
        
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': name,
                'last_name': 'Teacher',
                'is_staff': True  # Mark as staff so they can access admin if needed
            }
        )
        
        if created:
            user.set_password("password123")
            user.save()
            print(f"Created New User: {username}")
        else:
            print(f"Found User: {username}")

        # Ensure they are in the Staff Group
        user.groups.add(staff_group)

        # 3. FIX: Check and Create Staff Profile if Missing
        if not Staff.objects.filter(user=user).exists():
            Staff.objects.create(
                user=user,
                is_teaching_staff=True,
                employee_id=f"EMP{random.randint(1000, 9999)}",
                designation="Subject Teacher",
                department=dept_obj,
                joining_date=timezone.now().date()
            )
            print(f"   -> FIXED: Created missing Staff Profile for {username}")
        else:
            print(f"   -> OK: Staff Profile already exists.")

    print("\n--- REPAIR COMPLETED ---")

repair_data()
