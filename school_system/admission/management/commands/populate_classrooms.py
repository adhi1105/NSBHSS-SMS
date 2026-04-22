from django.core.management.base import BaseCommand
from admission.models import ClassRoom, Stream

class Command(BaseCommand):
    help = 'Safely configures Classrooms (A1-K2) handling existing data conflicts'

    def handle(self, *args, **kwargs):
        # 1. Define Streams
        streams_data = {
            "Biology Science": ["A", "B", "C", "D", "H"],
            "Home Science": ["E"],
            "Computer Science": ["F", "G"],
            "Humanities": ["I"],
            "Commerce": ["J", "K"]
        }

        self.stdout.write(self.style.WARNING("Configuring Classrooms..."))

        for stream_name, prefixes in streams_data.items():
            # Create Stream
            stream, _ = Stream.objects.get_or_create(name=stream_name)

            for prefix in prefixes:
                for division_num in ["1", "2"]: 
                    # Logic: 1 -> 11th, 2 -> 12th
                    std = 11 if division_num == "1" else 12
                    
                    # The Name we WANT (e.g., A1)
                    target_name = f"{prefix}{division_num}"

                    # --- THE FIX ---
                    # Look up by Standard & Division (The Unique Constraint)
                    # NOT by Name.
                    classroom, created = ClassRoom.objects.get_or_create(
                        standard=std,
                        division=prefix,
                        defaults={
                            'name': target_name,
                            'stream': stream
                        }
                    )

                    # If it existed but had a different name (e.g. "11-A"), update it to "A1"
                    if not created and classroom.name != target_name:
                        old_name = classroom.name
                        classroom.name = target_name
                        classroom.stream = stream # Ensure stream is correct
                        classroom.save()
                        self.stdout.write(f"  * Updated: {old_name} -> {target_name}")
                    elif created:
                        self.stdout.write(f"  + Created: {target_name}")
                    else:
                        self.stdout.write(f"  . Verified: {target_name}")

        self.stdout.write(self.style.SUCCESS("✅ Classrooms synced successfully!"))