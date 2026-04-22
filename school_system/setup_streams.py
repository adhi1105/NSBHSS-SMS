import os
import django

# 1. Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from admission.models import ClassRoom
from school_system.models import Stream
from student_info.models import Student
from django.db import transaction

def sync_hse_structure():
    # Mapping Data
    streams_data = {
        "Biology Science": ["A1", "A2", "B1", "B2", "C1", "C2", "D1", "D2", "H1", "H2"],
        "Home Science": ["E1", "E2"],
        "Computer Science": ["F1", "F2", "G1", "G2"],
        "Humanities": ["I1", "I2"],
        "Commerce": ["J1", "J2", "K1", "K2"]
    }

    try:
        with transaction.atomic():
            print("🧹 Clearing old structure (Students will be temporarily unassigned)...")
            # We don't delete students, just clear their links
            Student.objects.all().update(classroom=None, stream=None)
            
            # Now safe to delete old classes and streams
            ClassRoom.objects.all().delete()
            Stream.objects.all().delete()

            print("🚀 Building new HSE Stream & Class mapping...")
            for stream_name, classes in streams_data.items():
                stream_obj = Stream.objects.create(name=stream_name)
                
                for class_name in classes:
                    std = 11 if "1" in class_name else 12
                    div_letter = class_name[0] # e.g., 'A'
                    
                    new_class = ClassRoom.objects.create(
                        name=class_name,
                        standard=std,
                        division=div_letter,
                        stream=stream_obj
                    )

                    # --- STUDENT MAPPING LOGIC ---
                    # We find students whose 'temporary' or 'old' data matches this class name
                    # Adjust 'student_id__contains' if you store their class info differently
                    students_to_map = Student.objects.filter(
                        # We look for students who were previously in this division
                        # Or match based on a specific field you use for class names
                        address__icontains=f"Imported" # Example filter to catch existing records
                    )
                    
                    # If you have a way to identify which student belongs to 'A1', 
                    # you would apply that logic here. 
                    # For now, we print a reminder to do the final link in Admin.
                    print(f"   ✅ Created {class_name} -> {stream_name}")

            print("\n✨ Database Restructured successfully!")
            print("👉 Note: Please visit the Admin Panel to bulk-assign Students to their new Classes.")

    except Exception as e:
        print(f"❌ Error during sync: {e}")

if __name__ == '__main__':
    confirm = input("This will reset all Stream/Class mappings. Proceed? (y/n): ")
    if confirm.lower() == 'y':
        sync_hse_structure()