import os
import sys
import django
import random

# --- FIX: Add current directory to Python Path ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# --- Setup Django ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from django.contrib.auth.models import User, Group
from school_system.models import Subject
from staff.models import Staff

def run():
    subjects_list = [
        ('Mathematics', 'MATH'), ('Physics', 'PHY'), ('Chemistry', 'CHEM'),
        ('Biology', 'BIO'), ('Computer Science', 'CS'), ('English Literature', 'ENG'),
        ('History', 'HIST'), ('Geography', 'GEO'), ('Economics', 'ECO'),
        ('Physical Education', 'PE')
    ]

    staff_group, _ = Group.objects.get_or_create(name='Staff')
    print("--- STARTING DATA CREATION ---")

    for name, code in subjects_list:
        # A. Create Subject
        subject, _ = Subject.objects.get_or_create(name=name, defaults={'code': code})
        
        # B. Create User
        username = f"teacher_{code.lower()}"
        email = f"{username}@school.com"
        
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username, email=email, password="password123",
                first_name=name, last_name="Teacher"
            )
            user.groups.add(staff_group)
            
            # C. Create Staff Profile
            # Check if staff profile already exists to avoid errors
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

if __name__ == '__main__':
    run()
