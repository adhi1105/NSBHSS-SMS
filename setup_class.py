import os
import sys
import django

# --- 1. SETUP DJANGO ENVIRONMENT ---
# Get the directory where this script is located (e.g., /Users/xedbex/SMS/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Add this directory to Python's "search path"
sys.path.append(BASE_DIR)

# Point to your settings file (Change 'school_system' if your project folder has a different name)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')

# Initialize Django
try:
    django.setup()
except ModuleNotFoundError:
    print("❌ Error: Could not find 'school_system' folder.")
    print(f"   Current Search Path: {BASE_DIR}")
    print("   Please ensure this script is in the same folder as 'manage.py'.")
    sys.exit(1)

# --- IMPORTS (Must come AFTER django.setup) ---
from admission.models import ClassRoom
from school_system.models import Stream

def run_setup():
    print("------------------------------------------------")
    print("🚀  Starting Class 11 & 12 Setup...")
    print("------------------------------------------------")

    # 2. Define the Mapping
    # Format: Stream Name : [List of Divisions]
    stream_map = {
        'Biology Science':  ['A1','A2','B1','B2','C1','C2','D1','D2','H1','H2'],
        'Home Science':     ['E1','E2'],
        'Computer Science': ['F1','F2','G1','G2'],
        'Humanities':       ['I1','I2'],
        'Commerce':         ['J1','J2','K1','K2']
    }

    created_count = 0
    updated_count = 0

    # 3. Execution Loop
    for stream_name, divisions in stream_map.items():
        # A. Ensure Stream Exists
        stream_obj, _ = Stream.objects.get_or_create(name=stream_name)
        
        # B. Process Each Division
        for div_code in divisions:
            # --- LOGIC: 1 -> Class 11, 2 -> Class 12 ---
            if '1' in div_code:
                std = '11'
            elif '2' in div_code:
                std = '12'
            else:
                print(f"⚠️  Skipping unknown code format: {div_code}")
                continue
            # -------------------------------------------

            # C. Get or Create the Classroom
            # We look for a class matching Standard (11/12) and Division (A1/A2)
            classroom, created = ClassRoom.objects.get_or_create(
                standard=std,
                division=div_code,
            )

            # D. Update Stream & Seats
            # We update even if it exists, to ensure the Stream is correct
            if classroom.stream != stream_obj:
                classroom.stream = stream_obj
                classroom.total_seats = 60
                classroom.save()
                
                if created:
                    print(f"   ➕ Created: Class {std} - Div {div_code} ({stream_name})")
                    created_count += 1
                else:
                    print(f"   cw Updated: Class {std} - Div {div_code} -> {stream_name}")
                    updated_count += 1

    print("------------------------------------------------")
    print(f"🎉  Success! Processed {created_count + updated_count} classes.")
    print("------------------------------------------------")

if __name__ == '__main__':
    run_setup()