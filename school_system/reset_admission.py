import os
import glob
import django
from django.db import connection

# 1. Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_project.settings') # CHANGE 'school_project' to your actual project name!
django.setup()

def run_reset():
    print("🚀 Starting Admission App Reset...")

    # --- PART A: Delete Migration Files ---
    migration_path = os.path.join('admission', 'migrations', '*.py')
    files = glob.glob(migration_path)
    
    print(f"   Found {len(files)} migration files.")
    for f in files:
        if not f.endswith('__init__.py'):
            try:
                os.remove(f)
                print(f"   - Deleted: {f}")
            except Exception as e:
                print(f"   ! Error deleting {f}: {e}")

    # --- PART B: Clear Database History ---
    with connection.cursor() as cursor:
        print("\n   Cleaning Database Records...")
        
        # 1. Remove from django_migrations table
        cursor.execute("DELETE FROM django_migrations WHERE app = 'admission'")
        print("   - Cleared migration history.")

        # 2. Drop the tables (This deletes data!)
        #    Add any other models from admission app if needed
        tables = ['admission_classroom', 'admission_student', 'admission_subjectallocation']
        
        for table in tables:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"   - Dropped table: {table}")
            except Exception as e:
                print(f"   ! Could not drop {table} (might not exist).")

    print("\n✅ Reset Complete. You can now run makemigrations.")

if __name__ == '__main__':
    run_reset()