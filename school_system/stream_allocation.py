import os
import django
from django.db import transaction

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from staff.models import Staff, SubjectAllocation, Subject
from admission.models import ClassRoom

def allocate_by_stream_specialization():
    # Your exact mapping
    STREAM_MAP = {
        "Biology Science": ["Physics", "Chemistry", "Biology", "English", "Malayalam", "Hindi", "Arabic", "Mathematics"],
        "Home Science": ["Physics", "Chemistry", "Biology", "English", "Malayalam", "Hindi", "Arabic", "Home Science"],
        "Computer Science": ["Physics", "Chemistry", "English", "Malayalam", "Hindi", "Arabic", "Computer Science", "Mathematics"],
        "Commerce": ["Accountancy", "Business Studies", "Economics", "English", "Malayalam", "Hindi", "Arabic"],
        "Humanities": ["History", "Economics", "Political Science", "Sociology", "English", "Malayalam", "Hindi", "Arabic"]
    }

    try:
        with transaction.atomic():
            print("🧹 Phase 1: Clearing existing allocations...")
            SubjectAllocation.objects.all().delete()

            # Phase 2: Categorize Teachers by their ONE Subject
            all_staff = Staff.objects.all().exclude(designation__icontains="Physical Education")
            subject_pools = {}
            
            for teacher in all_staff:
                desig = (teacher.designation or "").lower()
                assigned_sub = None
                
                # Manual override for common HSST designations found in your logs
                if "hindi" in desig: assigned_sub = "Hindi"
                elif "arabic" in desig: assigned_sub = "Arabic"
                elif "computer application" in desig or "computer science" in desig: assigned_sub = "Computer Science"
                else:
                    # Match against all subjects in your streams
                    all_subs = set([s for sublist in STREAM_MAP.values() for s in sublist])
                    for s in all_subs:
                        if s.lower() in desig:
                            assigned_sub = s
                            break
                
                if assigned_sub:
                    if assigned_sub not in subject_pools:
                        subject_pools[assigned_sub] = []
                    # Track teacher and their load
                    subject_pools[assigned_sub].append({'staff': teacher, 'load': 0})

            # Phase 3: Allocate to Classrooms
            print("📝 Phase 3: Allocating subjects based on stream mapping...")
            classrooms = ClassRoom.objects.select_related('stream').all().order_by('standard', 'division')
            total_filled = 0

            for classroom in classrooms:
                stream_name = classroom.stream.name if classroom.stream else None
                required_subjects = STREAM_MAP.get(stream_name, [])

                for sub_name in required_subjects:
                    pool = subject_pools.get(sub_name, [])
                    assigned_teacher = None

                    # Rule: Max 11 classes per teacher (to cover 22 classes with current staff)
                    # We can lower this to 2 once you hire more staff
                    for expert_info in pool:
                        if expert_info['load'] < 11: 
                            assigned_teacher = expert_info['staff']
                            expert_info['load'] += 1
                            break
                    
                    if assigned_teacher:
                        subject_obj, _ = Subject.objects.get_or_create(name=sub_name)
                        SubjectAllocation.objects.create(
                            staff=assigned_teacher,
                            subject=subject_obj,
                            classroom=classroom
                        )
                        total_filled += 1

            print(f"\n✨ DONE! Filled {total_filled} subject slots.")
            print("🎯 Teachers are strictly locked to their designation subjects.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    allocate_by_stream_specialization()