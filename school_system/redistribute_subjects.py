import os
import django
from django.db import transaction

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from staff.models import Staff, SubjectAllocation, Subject
from admission.models import ClassRoom

def redistribute_subjects():
    try:
        with transaction.atomic():
            # 1. DELETE OLD ALLOCATIONS
            print("🧹 Clearing all current subject allocations...")
            SubjectAllocation.objects.all().delete()

            # 2. GET VALID STAFF (Excluding Physical Education staff)
            # We filter by designation or user-related fields if necessary
            teachers = Staff.objects.filter(
                is_teaching_staff=True,
                status='active'
            ).exclude(designation__icontains="Physical Education").exclude(user__first_name__icontains="Physical Education")

            # 3. GET VALID SUBJECTS (Excluding Physical Education)
            subjects = Subject.objects.exclude(name__icontains="Physical Education")

            # 4. GET ALL CLASSROOMS
            classrooms = ClassRoom.objects.all()

            if not teachers.exists() or not subjects.exists():
                print("❌ Error: Missing teachers or subjects to allocate.")
                return

            print(f"📊 Found {teachers.count()} teachers and {subjects.count()} subjects.")
            print(f"🏫 Allocating across {classrooms.count()} classrooms...")

            # 5. EQUAL DISTRIBUTION LOGIC
            # We create a list of all required assignments (Subject x Classroom)
            all_assignments = []
            for classroom in classrooms:
                for subject in subjects:
                    all_assignments.append((subject, classroom))

            # Distribute assignments among teachers
            teacher_list = list(teachers)
            num_teachers = len(teacher_list)
            
            count = 0
            for i, (subject, classroom) in enumerate(all_assignments):
                # Round-robin distribution to ensure equality
                assigned_teacher = teacher_list[i % num_teachers]
                
                SubjectAllocation.objects.create(
                    staff=assigned_teacher,
                    subject=subject,
                    classroom=classroom
                )
                count += 1

            print(f"\n✨ SUCCESS!")
            print(f"✅ Deleted old data.")
            print(f"✅ Created {count} new equalized allocations.")
            print(f"✅ Each teacher has roughly {count // num_teachers} subjects assigned.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    redistribute_subjects()