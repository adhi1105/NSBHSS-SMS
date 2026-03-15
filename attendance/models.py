from django.db import models
from django.utils import timezone
from student_info.models import Student
from admission.models import ClassRoom
from staff.models import Staff

# 1. THE SESSION LOG
class AttendanceLog(models.Model):
    """
    Represents the main session for a specific class, subject, and date.
    """
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='attendance_logs')
    # Use a string reference if the Subject model is in another app to avoid circular imports
    subject = models.ForeignKey('school_system.Subject', on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(default=timezone.now)
    taken_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-timestamp']
        # --- THE FIX: One Log per Class per Subject per Day ---
        constraints = [
            models.UniqueConstraint(
                fields=['classroom', 'subject', 'date'], 
                name='unique_attendance_log'
            )
        ]

    def __str__(self):
        subject_name = self.subject.name if self.subject else "General"
        return f"{self.classroom.name} - {subject_name} ({self.date})"

# 2. THE INDIVIDUAL ENTRIES
class AttendanceRecord(models.Model):
    """
    Individual status for each student within an AttendanceLog session.
    """
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('half_day', 'Half Day'),
    ]

    log = models.ForeignKey(AttendanceLog, on_delete=models.CASCADE, related_name='records')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        # --- THE FIX: One record per student per log ---
        constraints = [
            models.UniqueConstraint(
                fields=['log', 'student'], 
                name='unique_student_attendance_record'
            )
        ]

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.status}"