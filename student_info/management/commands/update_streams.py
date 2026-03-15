from django.core.management.base import BaseCommand
from student_info.models import Student

class Command(BaseCommand):
    help = 'Updates the Stream field for all students based on their Classroom'

    def handle(self, *args, **kwargs):
        students = Student.objects.all()
        updated_count = 0
        
        self.stdout.write(self.style.WARNING(f"Checking {students.count()} students for missing Streams..."))

        for student in students:
            # 1. Check if student has a classroom
            if student.classroom:
                # 2. Get the stream from the classroom
                correct_stream = student.classroom.stream
                
                # 3. Update if missing or incorrect
                if correct_stream and student.stream != correct_stream:
                    student.stream = correct_stream
                    student.save()
                    updated_count += 1
                    # Optional: Print every 50 updates to avoid spam
                    if updated_count % 50 == 0:
                        self.stdout.write(f"  > Updated {updated_count} records...")

        self.stdout.write(self.style.SUCCESS(f"✅ Successfully updated Streams for {updated_count} students!"))