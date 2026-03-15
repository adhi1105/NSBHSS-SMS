import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from django.test import RequestFactory
from student_info.models import Student
from django.template.loader import render_to_string
import traceback

student = Student.objects.first()
factory = RequestFactory()
request = factory.get('/')
request.user = student.user

try:
    html = render_to_string('profile.html', {'profile': student, 'user': request.user}, request=request)
    print("SUCCESS: Template rendered without SyntaxError")
except Exception as e:
    traceback.print_exc()
