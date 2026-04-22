import os
import django

# 1. Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from django.contrib.auth.models import User, Group
from staff.models import Staff, SubjectAllocation
from admission.models import ClassRoom
from school_system.models import Subject

def fix_all_teachers():
    print("🛠️  Starting Safer Global Teacher Fix...")
    
    # 2. Ensure the Teacher Group exists
    teacher_group, _ = Group.objects.get_or_create(name='Teacher')
    
    # 3. Get a default class and subject
    default_class = ClassRoom.objects.first()
    default_subject = Subject.objects.first()
    
    if not default_class or not default_subject:
        print("❌ Error: You need at least one Class and Subject in the DB.")
        return

    # 4. Process all teaching staff
    teaching_staff = Staff.objects.filter(is_teaching_staff=True)
    
    for staff in teaching_staff:
        # A. Add to Teacher Group
        staff.user.groups.add(teacher_group)
        
        # B. Check for ANY existing allocation
        if not SubjectAllocation.objects.filter(staff=staff).exists():
            # Use get_or_create to avoid UNIQUE constraint crashes
            # This ensures Anjali and others get assigned without duplicates
            allocation, created = SubjectAllocation.objects.get_or_create(
                classroom=default_class,
                subject=default_subject,
                defaults={'staff': staff} # If it doesn't exist, assign this staff
            )
            
            if created:
                print(f"✅ Created new allocation for: {staff.user.get_full_name()}")
            else:
                # If someone else already teaches this, we need to assign a DIFFERENT subject
                # to this specific teacher to bypass the Unique Constraint
                print(f"⚠️  {default_subject} in {default_class} is already taken. Checking for alternatives...")
                
                # Try to find a subject that isn't allocated to this class yet
                existing_subjects = SubjectAllocation.objects.filter(classroom=default_class).values_list('subject_id', flat=True)
                alt_subject = Subject.objects.exclude(id__in=existing_subjects).first()
                
                if alt_subject:
                    SubjectAllocation.objects.create(staff=staff, classroom=default_class, subject=alt_subject)
                    print(f"✅ Assigned alternative: {alt_subject} in {default_class}")
                else:
                    print(f"❌ Could not find a free subject for {staff.user.get_full_name()}. Assign manually in Admin.")
        else:
            print(f"ℹ️  {staff.user.get_full_name()} already has allocations.")

    print("\n🚀 System synchronized!")

if __name__ == '__main__':
    fix_all_teachers()