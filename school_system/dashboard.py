from django.contrib.auth.models import User
from student_info.models import Student
from staff.models import Staff
from admission.models import AdmissionApplication
from school_system.models import Stream
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count

try:
    from attendance.models import AttendanceRecord
except ImportError:
    AttendanceRecord = None

def get_dashboard_stats(request):
    """
    Returns high-end analytical data for the Unfold dashboard.
    """
    today = timezone.now().date()
    
    # 1. Attendance Trend (Last 7 Days)
    attendance_chart = []
    if AttendanceRecord:
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            count = AttendanceRecord.objects.filter(log__date=date, status='present').count()
            attendance_chart.append({"label": date.strftime("%a"), "value": count})
    
    # 2. Stream Distribution (Students per Stream)
    stream_distribution = []
    streams = Stream.objects.annotate(student_count=Count('student_set'))
    for s in streams:
        stream_distribution.append({"label": s.name, "value": s.student_count})

    return {
        "metrics": [
            {
                "title": "Total Students",
                "value": Student.objects.count(),
                "footer": "Active enrollments",
                "icon": "groups",
            },
            {
                "title": "Total Staff",
                "value": Staff.objects.filter(user__is_active=True).count(),
                "footer": "Teaching & Admin",
                "icon": "badge",
            },
            {
                "title": "Pending Admissions",
                "value": AdmissionApplication.objects.filter(status="Pending").count(),
                "footer": "Awaiting review",
                "icon": "app_registration",
            },
        ],
        "charts": [
            {
                "title": "Attendance Trend (Last 7 Days)",
                "type": "bar",
                "data": attendance_chart,
            },
            {
                "title": "Students by Stream",
                "type": "pie",
                "data": stream_distribution,
            }
        ]
    }
