from django.core.management.base import BaseCommand
from student_info.models import Student
from admission.models import ClassRoom

class Command(BaseCommand):
    help = 'Fixes students who are not showing up in their classes'

    def handle(self, *args, **kwargs):
        # 1. Find orphans (Students with no classroom)
        orphans = Student.objects.filter(classroom__isnull=True)
        total_students = Student.objects.count()
        
        self.stdout.write(f"Total Students: {total_students}")
        self.stdout.write(self.style.WARNING(f"Students without Class: {orphans.count()}"))

        fixed_count = 0

        # 2. Try to fix them using their ID
        # Example ID: "S26-A1-105" -> We can extract "A1"
        for student in orphans:
            try:
                # Extract parts: "S26", "A1", "105"
                parts = student.student_id.split('-')
                
                if len(parts) >= 2:
                    batch_code = parts[1] # "A1"
                    
                    # Find the classroom
                    # Try looking by Division (A1) or Name (11-A1)
                    classroom = ClassRoom.objects.filter(division=batch_code).first()
                    
                    if not classroom:
                        classroom = ClassRoom.objects.filter(name__icontains=batch_code).first()

                    if classroom:
                        student.classroom = classroom
                        student.save()
                        fixed_count += 1
                        self.stdout.write(f"  > Fixed: {student.user.username} -> Assigned to {classroom.name}")
                    else:
                        self.stdout.write(self.style.ERROR(f"  X Could not find class for code '{batch_code}'"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  X Error processing {student.student_id}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"✅ Repair Complete! Fixed {fixed_count} students."))