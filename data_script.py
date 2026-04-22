from django.contrib.auth.models import User, Group
from school_system.models import Subject
from staff.models import Staff
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
        # Create Subject
        subject, created = Subject.objects.get_or_create(name=name, defaults={'code': code})
        
        # Create User
        username = f"teacher_{code.lower()}"
        email = f"{username}@school.com"
        
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username, email=email, password="password123",
                first_name=name, last_name="Teacher"
            )
            user.groups.add(staff_group)
            
            # Create Staff Profile
            if not Staff.objects.filter(user=user).exists():
                Staff.objects.create(
                    user=user, is_teaching_staff=True,
                    employee_id=f"EMP{random.randint(1000, 9999)}",
                    designation="Subject Teacher", department=name
                )
            print(f"Created: {username}")
        else:
            print(f"Exists: {username}")

    print("\n--- COMPLETED SUCCESSFULLY ---")

# Run the function
create_data()
