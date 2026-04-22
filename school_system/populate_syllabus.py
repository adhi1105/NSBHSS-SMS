import os
import django

# --- 1. SETUP DJANGO ENVIRONMENT ---
# This allows the script to access your database models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from school_system.models import Stream, Subject

def run_script():
    print("Initializing Kerala Syllabus Structure...")

    # --- 2. Create Streams ---
    science, _ = Stream.objects.get_or_create(name="Science")
    commerce, _ = Stream.objects.get_or_create(name="Commerce")
    humanities, _ = Stream.objects.get_or_create(name="Humanities")

    print(f"Streams Confirmed: {science}, {commerce}, {humanities}")

    # --- 3. Define Syllabus Data ---
    # Format: ("Subject Name", "Type", Is_Practical, [List of Streams])
    syllabus = [
        # LANGUAGES (Available to All)
        ("English", "Language", False, [science, commerce, humanities]),
        ("Malayalam", "Language", False, [science, commerce, humanities]),
        ("Hindi", "Language", False, [science, commerce, humanities]),
        ("Arabic", "Language", False, [science, commerce, humanities]),
        ("Sanskrit", "Language", False, [science, commerce, humanities]),

        # SCIENCE
        ("Physics", "Core", True, [science]),
        ("Chemistry", "Core", True, [science]),
        ("Biology", "Core", True, [science]),
        ("Mathematics", "Core", False, [science, commerce]), # Shared with Commerce
        ("Computer Science", "Elective", True, [science]),
        
        # COMMERCE
        ("Accountancy", "Core", True, [commerce]),
        ("Business Studies", "Core", False, [commerce]),
        ("Economics", "Core", False, [commerce, humanities]), # Shared with Humanities
        ("Computer Applications", "Elective", True, [commerce, humanities]),
        
        # HUMANITIES
        ("History", "Core", False, [humanities]),
        ("Political Science", "Core", False, [humanities]),
        ("Sociology", "Elective", False, [humanities]),
        ("Psychology", "Elective", True, [humanities]),
    ]

    # --- 4. Insert Data ---
    count = 0
    for name, s_type, is_prac, stream_list in syllabus:
        # Create or Get the subject
        sub, created = Subject.objects.get_or_create(
            name=name,
            defaults={'subject_type': s_type, 'is_practical': is_prac}
        )
        
        # Ensure correct subject type and practical status if it already existed
        if not created:
            sub.subject_type = s_type
            sub.is_practical = is_prac
            sub.save()

        # Link to Streams
        for stream in stream_list:
            sub.streams.add(stream)
        
        if created:
            print(f"  [+] Created: {name}")
            count += 1
        else:
            print(f"  [.] Updated: {name}")

    print(f"\nSuccess! {count} new subjects added to the syllabus.")

if __name__ == "__main__":
    run_script()