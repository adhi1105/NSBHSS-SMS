from django.core.management.base import BaseCommand
from admission.models import ClassRoom
from school_system.models import Subject
from staff.models import SubjectAllocation
from django.db import transaction

class Command(BaseCommand):
    help = 'Syncs subject allocations according to stream specialization'

    def handle(self, *args, **options):
        # Strict Master Mapping
        STREAM_MAPPING = {
            'Home Science': [
                'Physics', 'Chemistry', 'Biology', 'English', 
                'Malayalam', 'Hindi', 'Home Science'
            ],
            'Biology Science': [
                'Physics', 'Chemistry', 'Biology', 'English', 
                'Malayalam', 'Hindi', 'Mathematics'
            ],
            'Computer Science': [
                'Physics', 'Chemistry', 'English', 
                'Malayalam', 'Hindi', 'Computer Science', 'Mathematics'
            ],
            'Commerce': [
                'Accountancy', 'Business Studies', 'Economics', 
                'English', 'Malayalam', 'Hindi'
            ],
            'Humanities': [
                'History', 'Economics', 'Political Science', 
                'Sociology', 'English', 'Malayalam', 'Hindi'
            ]
        }

        self.stdout.write(self.style.MIGRATE_HEADING("Starting Subject Mapping Sync..."))

        with transaction.atomic():
            # Apply only to Higher Secondary (11 & 12)
            classrooms = ClassRoom.objects.filter(standard__in=[11, 12])
            
            for classroom in classrooms:
                stream_name = classroom.stream.name
                
                if stream_name not in STREAM_MAPPING:
                    self.stdout.write(self.style.WARNING(f"Skipping {classroom}: Stream '{stream_name}' not defined in mapping."))
                    continue

                allowed_subject_names = STREAM_MAPPING[stream_name]
                
                # 1. DELETE: Remove allocations that don't belong to this stream
                invalid_allocations = SubjectAllocation.objects.filter(classroom=classroom).exclude(subject__name__in=allowed_subject_names)
                
                for alloc in invalid_allocations:
                    sub_name = alloc.subject.name
                    alloc.delete()
                    self.stdout.write(self.style.ERROR(f"Removed: {sub_name} from {classroom} (Not in {stream_name} specialization)"))

                # 2. VALIDATE: Check if required subjects exist for this class
                for sub_name in allowed_subject_names:
                    subject = Subject.objects.filter(name=sub_name).first()
                    if subject:
                        exists = SubjectAllocation.objects.filter(classroom=classroom, subject=subject).exists()
                        if not exists:
                            # We just notify, because we can't auto-assign a teacher without knowing who it is
                            self.stdout.write(f"Missing Allocation: {classroom} needs {sub_name}")
                    else:
                        self.stdout.write(self.style.WARNING(f"Subject '{sub_name}' does not exist in the Subject database."))

        self.stdout.write(self.style.SUCCESS("\n✅ Subject specialization sync completed successfully."))