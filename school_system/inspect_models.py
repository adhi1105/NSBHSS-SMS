import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from student_info.models import Student
from staff.models import Staff

print("\n--- Student Fields ---")
student = Student.objects.first()
if student:
    print([f.name for f in student._meta.get_fields() if not f.is_relation or f.one_to_one or (f.many_to_one and f.related_model)])
    print(f"Sample dict keys: {[k for k in student.__dict__.keys() if not k.startswith('_')]}")

print("\n--- Staff Fields ---")
staff = Staff.objects.first()
if staff:
    print([f.name for f in staff._meta.get_fields() if not f.is_relation or f.one_to_one or (f.many_to_one and f.related_model)])
    print(f"Sample dict keys: {[k for k in staff.__dict__.keys() if not k.startswith('_')]}")
