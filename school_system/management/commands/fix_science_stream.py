from django.core.management.base import BaseCommand
from school_system.models import Stream, Subject

class Command(BaseCommand):
    help = 'Consolidates Biology, Computer Science, and Home Science into a single Science stream'

    def handle(self, *args, **kwargs):
        self.stdout.write("🔄 Starting Stream Consolidation...")

        # 1. Get or Create the single Master 'Science' Stream
        science_stream, created = Stream.objects.get_or_create(name="Science")
        if created:
            self.stdout.write(self.style.SUCCESS(f"   Created new stream: 'Science'"))
        else:
            self.stdout.write(f"   Found existing stream: 'Science'")

        # 2. Define ALL subjects for the Science Stream
        science_subjects = [
            "Physics", "Chemistry", "Mathematics",  # Core
            "Biology", "Computer Science", "Home Science", # The Electives
            "Electronics", "Statistics", "Psychology"      # Extras
        ]

        # 3. Link Subjects
        for name in science_subjects:
            # We use get_or_create to allow the script to run even if subjects are missing
            subject, _ = Subject.objects.get_or_create(name=name)
            
            # Add to Science stream
            subject.streams.add(science_stream)
            self.stdout.write(f"   Linked '{name}' -> Science")

        # 4. Cleanup: Remove the old fragmented streams
        old_streams = ["Biology Science", "Computer Science", "Home Science"]
        deleted_count, _ = Stream.objects.filter(name__in=old_streams).delete()

        if deleted_count > 0:
            self.stdout.write(self.style.WARNING(f"   🗑️  Deleted {deleted_count} old fragmented streams."))
        
        self.stdout.write(self.style.SUCCESS("✅ Successfully consolidated Science Stream!"))