from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from student_info.models import Student
from admission.models import ClassRoom
from school_system.models import Subject 

# --- 1. CONFIGURATION: Grading Rules ---
class GradingScale(models.Model):
    grade_name = models.CharField(max_length=5) # e.g. "A+"
    min_percentage = models.IntegerField()      # e.g. 90
    max_percentage = models.IntegerField()      # e.g. 100
    grade_point = models.DecimalField(max_digits=3, decimal_places=2) # e.g. 4.0 or 10.0
    description = models.CharField(max_length=50, blank=True) # e.g. "Outstanding"

    def __str__(self):
        return f"{self.grade_name} ({self.min_percentage}-{self.max_percentage}%)"

    class Meta:
        ordering = ['-min_percentage'] # Sorts High to Low automatically

# --- 2. SETUP: Exam Schedule ---
class Exam(models.Model):
    EXAM_TYPES = [
        ('MID', 'Mid-Term'),
        ('FINAL', 'Final Exam'),
        ('TEST', 'Monthly Test'),
    ]

    name = models.CharField(max_length=100) # e.g. "Final Term 2026"
    exam_type = models.CharField(max_length=10, choices=EXAM_TYPES, default='MID')
    academic_session = models.CharField(max_length=20, default="2025-2026")
    start_date = models.DateField()
    end_date = models.DateField()
    
    # --- SAFETY CONTROLS ---
    is_active = models.BooleanField(default=True)      # Visible to Teachers for Entry?
    is_locked = models.BooleanField(default=False)     # "Lock" marks after verification?
    is_published = models.BooleanField(default=False)  # Visible to Students/Parents?
    
    weightage = models.IntegerField(default=100, help_text="Percentage weight in final result")

    def __str__(self):
        return f"{self.name} ({self.academic_session})"

# --- 3. EXECUTION: Marks Entry ---
class Result(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    
    # Who entered this mark? (Audit Trail)
    entered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    
    # Auto-Calculated Fields
    grade = models.CharField(max_length=5, blank=True)
    grade_point = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    is_passed = models.BooleanField(default=False)
    
    remarks = models.CharField(max_length=200, blank=True, help_text="Teacher's specific comment")

    class Meta:
        unique_together = ('exam', 'student', 'subject')

    def save(self, *args, **kwargs):
        # 1. Convert marks to numbers (Fixes "str / float" error)
        try:
            obtained = float(self.marks_obtained)
            total = float(self.total_marks)
        except (ValueError, TypeError):
            obtained = 0.0
            total = 100.0

        # 2. Calculate Percentage
        percentage = 0
        if total > 0:
            percentage = (obtained / total) * 100
        
        # 3. Dynamic Grade Lookup
        scale = GradingScale.objects.filter(
            min_percentage__lte=percentage, 
            max_percentage__gte=percentage
        ).first()

        if scale:
            self.grade = scale.grade_name
            self.grade_point = scale.grade_point
            self.is_passed = percentage >= 40 
        else:
            self.grade = "N/A"
            self.is_passed = False

        # 4. Save the clean data back to the object
        self.marks_obtained = obtained
        self.total_marks = total
        
        super().save(*args, **kwargs)