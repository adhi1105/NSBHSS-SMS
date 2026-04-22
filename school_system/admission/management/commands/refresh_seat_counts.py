from django.core.management.base import BaseCommand
from admission.models import ClassRoom

class Command(BaseCommand):
    help = 'Recalculates static occupied_seats count'

    def handle(self, *args, **kwargs):
        classrooms = ClassRoom.objects.all()
        for cls in classrooms:
            # Manually count students
            actual_count = cls.students.filter(status='pursuing').count()
            
            # Update the static field
            cls.occupied_seats = actual_count
            cls.save()
            self.stdout.write(f"Updated {cls.name}: {actual_count} seats occupied.")