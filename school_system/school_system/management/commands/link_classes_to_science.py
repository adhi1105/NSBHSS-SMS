from django.core.management.base import BaseCommand
from admission.models import ClassRoom
from school_system.models import Stream, Subject

class Command(BaseCommand):
    help = 'Links specific Science classrooms (Bio/CS/Home) to the master Science stream'

    def handle(self, *args, **kwargs):
        self.stdout.write("🔄 Linking Classrooms to Master Science Stream...")

        # 1. Get the Master 'Science' Stream
        science_stream, _ = Stream.objects.get_or_create(name="Science")
        
        # 2. Define keywords to identify your science classes
        # Adjust these keywords based on how you named your classes (e.g., "11-A Computer Sci")
        science_keywords = ["Computer Science", "Biology", "Home Science", "Bio", "CS"]

        # 3. Find and Update Classrooms
        count = 0
        all_classes = ClassRoom.objects.all()
        
        for classroom in all_classes:
            # Check if class name contains any science keyword
            # e.g. If class name is "12-A Computer Science"
            if any(keyword.lower() in classroom.name.lower() for keyword in science_keywords):
                
                # Update the stream to the Master 'Science' stream
                classroom.stream = science_stream
                classroom.save()
                
                self.stdout.write(f"   Mapped '{classroom.name}' -> Science Stream")
                count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Successfully updated {count} classrooms to Science!"))