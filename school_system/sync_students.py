import os
import django
from django.db import transaction

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from admission.models import ClassRoom
from student_info.models import Student

def distribute_students_perfectly():
    try:
        with transaction.atomic():
            # 1. Get all 22 classes ordered by name (A1, A2, B1...)
            classes = list(ClassRoom.objects.all().order_by('name'))
            if len(classes) != 22:
                print(f"⚠️ Warning: Found {len(classes)} classes instead of 22. Checking count...")
            
            # 2. Get all 220 students
            students = list(Student.objects.all().order_by('id'))
            total_students = len(students)
            print(f"📊 Found {total_students} students to distribute across {len(classes)} classes.")

            if total_students == 0:
                print("❌ No students found!")
                return

            # 3. Distribution & ID Update
            # We want exactly 10 per class (220 / 22 = 10)
            students_per_class = 10
            
            updated_count = 0
            for i, student in enumerate(students):
                # Determine which class this student belongs to
                class_index = i // students_per_class
                
                # Safety check for extra students
                if class_index >= len(classes):
                    class_index = len(classes) - 1
                
                target_cls = classes[class_index]
                
                # Roll number logic (1 to 10)
                roll_no = (i % students_per_class) + 1
                new_id = f"{target_cls.name}-{roll_no:02d}"
                
                # Update the database
                # Using update() is safer than save() when fields are missing
                Student.objects.filter(id=student.id).update(
                    classroom=target_cls,
                    stream=target_cls.stream,
                    student_id=new_id  # Ensure this matches your model field name
                )
                updated_count += 1

            print(f"\n✨ SUCCESS!")
            print(f"✅ Distributed {updated_count} students.")
            print(f"✅ Each class now has approximately {students_per_class} students.")
            print(f"✅ Example ID format: {classes[0].name}-01")

    except Exception as e:
        print(f"❌ Error during distribution: {e}")

if __name__ == '__main__':
    distribute_students_perfectly()