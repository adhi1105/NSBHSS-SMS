from django.core.management.base import BaseCommand
from admission.models import ClassRoom

class Command(BaseCommand):
    help = "Lists all classrooms to debug naming issues"

    def handle(self, *args, **kwargs):
        classes = ClassRoom.objects.all()
        self.stdout.write(f"Total Classrooms Found: {classes.count()}")
        self.stdout.write("------------------------------------------------")
        self.stdout.write(f"{'ID':<5} | {'Name':<15} | {'Std':<5} | {'Div':<5}")
        self.stdout.write("------------------------------------------------")
        
        for c in classes:
            # Prints the exact data stored in DB
            self.stdout.write(f"{c.id:<5} | {c.name:<15} | {c.standard:<5} | {c.division:<5}")