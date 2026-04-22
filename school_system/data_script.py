from django.contrib.auth.models import User, Group
from school_system.models import Subject
from staff.models import Staff, Department
from django.utils import timezone  # <--- Import timezone
import random

def create_data():
    subjects_list = [
        ('Mathematics', 'MATH'), ('Physics', 'PHY'), ('Chemistry', 'CHEM'),
        ('Biology', 'BIO'), ('Computer Science', 'CS'), ('English Literature', 'ENG'),
        ('History', 'HIST'), ('Geography', 'GEO'), ('Economics', 'ECO'),
        ('Physical Education', 'PE')
    ]

    staff_group, _ = Group.objects.get_or_create(name='Staff')
    print("--- STARTING DATA CREATION ---")

    for name, code in subjects_list:
        # 1. Create Subject
        subject, _ = Subject.objects.get_or_create(name=name, defaults={'code': code})
        
        # 2. Create/Get Department
        dept_obj, _ = Department.objects.get_or_create(name=name)

        # 3. Create User
        username = f"teacher_{code.lower()}"
        email = f"{username}@school.com"
        
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username, email=email, password="password123",
                first_name=name, last_name="Teacher"
            )
            user.groups.add(staff_group)
            
            # 4. Create Staff Profile (With Joining Date)
            if not Staff.objects.filter(user=user).exists():
                Staff.objects.create(
                    user=user,
                    is_teaching_staff=True,
                    employee_id=f"EMP{random.randint(1000, 9999)}",
                    designation="Subject Teacher",
                    department=dept_obj,
                    joining_date=timezone.now().date()  # <--- THE FIX
                )
            print(f"Created: {username}")
        else:
            print(f"Exists: {username}")

    print("\n--- COMPLETED SUCCESSFULLY ---")

create_data()
