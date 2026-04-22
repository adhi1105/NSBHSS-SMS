import os
import re

# 1. Configuration
TARGET_APP = 'admission'
NEW_MIGRATION_NAME = '0001_initial'
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def fix_project_dependencies():
    print(f"🚀 Scanning project for broken links to '{TARGET_APP}'...")
    count = 0

    # Walk through all folders in the project
    for root, dirs, files in os.walk(PROJECT_ROOT):
        if 'migrations' in root and 'site-packages' not in root:
            for file in files:
                if file.endswith('.py') and file != '__init__.py':
                    file_path = os.path.join(root, file)
                    fix_file(file_path)

def fix_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to find dependencies like: ('admission', '0002_old_stuff')
    # We capture the line to ensure we only replace inside the dependencies list
    pattern = re.compile(rf"\('{TARGET_APP}',\s*'([^']+)'\)")
    
    matches = pattern.findall(content)
    if not matches:
        return

    # Check if any match is NOT the new initial
    needs_fix = False
    for match in matches:
        if match != NEW_MIGRATION_NAME:
            needs_fix = True
            print(f"   🔧 Fixing: {os.path.basename(file_path)} (Found reference to '{match}')")

    if needs_fix:
        # Replace ANY reference to admission migrations with '0001_initial'
        new_content = pattern.sub(f"('{TARGET_APP}', '{NEW_MIGRATION_NAME}')", content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

if __name__ == "__main__":
    fix_project_dependencies()
    print("\n✅ All dependencies updated to point to '0001_initial'.")
    print("👉 Now run: python manage.py makemigrations admission")