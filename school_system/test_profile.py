import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from django.test import RequestFactory
from student_info.models import Student
from django.template.loader import render_to_string
import traceback
from datetime import datetime

student = Student.objects.first()
factory = RequestFactory()
request = factory.get('/')
request.user = student.user
classroom = student.classroom

context = {
    'profile': student,
    'user': request.user,
    'role': 'Student',
    'academic': {
        'class': classroom,
        'stream': 'SCIENCE',
        'subjects': ['Maths', 'Physics']
    }
}

try:
    html = render_to_string('profile.html', context, request=request)
    print("SUCCESS: Template rendered without SyntaxError")
except Exception as e:
    traceback.print_exc()
