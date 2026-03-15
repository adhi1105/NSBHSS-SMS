import os
import django
from django.db import transaction

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from admission.models import ClassRoom
from student_info.models import Student

def make_clean_ids():
    try:
        with transaction.atomic():
            print("🔢 Generating Clean Numerical IDs...")
            classes = ClassRoom.objects.all().order_by('name')
            total = 0

            for cls in classes:
                # cls.standard (11/12) and cls.division (A, B, C...)
                # We use these to build the prefix
                std_prefix = str(cls.standard)
                div_prefix = str(cls.division).upper()
                
                students = Student.objects.filter(classroom=cls).order_by('id')
                
                for index, student in enumerate(students, start=1):
                    # Format: [Standard][Division][RollNo] 
                    # Examples: 11A1, 11A10, 12B5
                    clean_id = f"{std_prefix}{div_prefix}{index}"
                    
                    Student.objects.filter(id=student.id).update(student_id=clean_id)
                    total += 1

            print(f"✅ Successfully updated {total} Student IDs.")
            print(f"🚀 New Format: {clean_id} (Standard + Division + Roll No)")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    make_clean_ids()