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
    'student': student,
    'current_class': None,
    'next_class': None,
    'overdue_books': [],
    'transport_status': "Active", 
    'attendance_percentage': 85.5, 
    'total_days': 100,
    'present_days': 85,
    'fees_due': 1000
}

try:
    html = render_to_string('dashboard_student.html', context, request=request)
    print("SUCCESS: Template rendered without SyntaxError")
except Exception as e:
    traceback.print_exc()
