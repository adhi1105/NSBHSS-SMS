from django.core.management.base import BaseCommand
from admission.models import ClassRoom
from school_system.models import Subject
from staff.models import Staff, SubjectAllocation
from django.db import transaction
from django.db.models import Count

class Command(BaseCommand):
    help = 'Fixes all missing allocations based on stream specialization'

    def handle(self, *args, **options):
        STREAM_MAPPING = {
            'Home Science': ['Physics', 'Chemistry', 'Biology', 'English', 'Malayalam', 'Hindi', 'Home Science'],
            'Biology Science': ['Physics', 'Chemistry', 'Biology', 'English', 'Malayalam', 'Hindi', 'Mathematics'],
            'Computer Science': ['Physics', 'Chemistry', 'English', 'Malayalam', 'Hindi', 'Computer Science', 'Mathematics'],
            'Commerce': ['Accountancy', 'Business Studies', 'Economics', 'English', 'Malayalam', 'Hindi'],
            'Humanities': ['History', 'Economics', 'Political Science', 'Sociology', 'English', 'Malayalam', 'Hindi']
        }

        with transaction.atomic():
            # Get a default staff member to act as placeholder if needed
            # Or you can leave teacher=None if your model allows nulls
            default_staff = Staff.objects.first() 

            for classroom in ClassRoom.objects.filter(standard__in=[11, 12]):
                stream_name = classroom.stream.name
                if stream_name not in STREAM_MAPPING:
                    continue

                required_subjects = STREAM_MAPPING[stream_name]

                # 1. REMOVE INVALID: Subjects not belonging to this stream
                SubjectAllocation.objects.filter(classroom=classroom).exclude(subject__name__in=required_subjects).delete()

                # 2. ADD MISSING: Create allocations so they show in timetable
                for sub_name in required_subjects:
                    subject = Subject.objects.filter(name__iexact=sub_name).first()
                    if subject:
                        # get_or_create ensures we don't double up
                        alloc, created = SubjectAllocation.objects.get_or_create(
                            classroom=classroom,
                            subject=subject,
                            defaults={'staff': default_staff} # Temporary assignment
                        )
                        if created:
                            self.stdout.write(self.style.SUCCESS(f"Created allocation: {sub_name} for {classroom}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"Subject '{sub_name}' missing from Master Database!"))

        self.stdout.write(self.style.SUCCESS("All allocations synchronized with Stream Specializations."))

def get_least_burdened_teacher(subject_name):
    # Find teachers qualified for this subject
    # This assumes your Staff model has a 'department' or 'specialization' field
    teachers = Staff.objects.filter(department__name__icontains=subject_name.split('/')[0])
    
    # Annotate with current period count from TimetableEntry
    return teachers.annotate(
        workload=Count('timetableentry')
    ).order_by('workload').first()        