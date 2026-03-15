import os
import django
from django.db import transaction

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from admission.models import ClassRoom
from student_info.models import Student

def alphabetical_sync():
    try:
        with transaction.atomic():
            # 1. PREVENT UNIQUE ERROR: Temporarily clear all student_ids
            print("🧹 Clearing current IDs to avoid conflicts...")
            students_all = Student.objects.all()
            for student in students_all:
                # Assigning a temporary unique ID using the primary key
                Student.objects.filter(id=student.id).update(student_id=f"TEMP_{student.id}")

            # 2. Get all 22 classes in order
            classes = list(ClassRoom.objects.all().order_by('standard', 'division'))
            
            # 3. Get students sorted by First Name
            print("📊 Sorting students alphabetically...")
            students_sorted = list(Student.objects.all().order_by('user__first_name'))
            
            total_students = len(students_sorted)
            if total_students == 0:
                print("❌ No students found!")
                return

            # 4. Distribute (10 students per class)
            students_per_class = 10
            
            print(f"🔗 Re-linking {total_students} students...")
            for i, student in enumerate(students_sorted):
                class_index = i // students_per_class
                if class_index >= len(classes):
                    class_index = len(classes) - 1
                
                target_cls = classes[class_index]
                
                # Roll number (1-10)
                roll_no = (i % students_per_class) + 1
                
                # Create the Clean Short ID (Standard + Division + RollNo)
                clean_id = f"{target_cls.standard}{target_cls.division}{roll_no}"
                
                # Final Update
                Student.objects.filter(id=student.id).update(
                    classroom=target_cls,
                    stream=target_cls.stream,
                    student_id=clean_id
                )

            print(f"✅ SUCCESS! {total_students} students sorted and assigned unique IDs.")
            print(f"🚀 New ID format: {clean_id}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    alphabetical_sync()