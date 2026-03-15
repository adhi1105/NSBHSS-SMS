import string
from django.db import models
from django.contrib.auth.models import User
from school_system.models import Stream, Subject

# 1. CLASSROOM
class ClassRoom(models.Model):
    STANDARD_CHOICES = [(str(i), str(i)) for i in range(1, 13)]
    
    # Specific Divisions based on Kerala Syllabus Stream Mapping
    DIVISION_CHOICES = [
        ('A1', 'A1'), ('A2', 'A2'), ('B1', 'B1'), ('B2', 'B2'),
        ('C1', 'C1'), ('C2', 'C2'), ('D1', 'D1'), ('D2', 'D2'),
        ('E1', 'E1'), ('E2', 'E2'), ('F1', 'F1'), ('F2', 'F2'),
        ('G1', 'G1'), ('G2', 'G2'), ('H1', 'H1'), ('H2', 'H2'),
        ('I1', 'I1'), ('I2', 'I2'), ('J1', 'J1'), ('J2', 'J2'),
        ('K1', 'K1'), ('K2', 'K2'), ('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D') 
    ]

    standard = models.CharField(max_length=5, choices=STANDARD_CHOICES)
    division = models.CharField(max_length=5, choices=DIVISION_CHOICES)
    
    # Link to Stream (e.g., 11-A1 is linked to Science)
    stream = models.ForeignKey(Stream, on_delete=models.SET_NULL, null=True, blank=True)
    
    # --- NEW: Class Teacher Assignment ---
    class_teacher = models.OneToOneField(
        'staff.Staff', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='class_teacher_of',
        help_text="The teacher in charge of this specific class."
    )
    
    name = models.CharField(max_length=100, blank=True, editable=False)
    total_seats = models.IntegerField(default=60)
    
    # --- DYNAMIC SEAT COUNTING ---
    @property
    def occupied_seats(self):
        """Returns real-time count of students assigned to this class"""
        from student_info.models import Student
        # This counts all students linked to this classroom
        return Student.objects.filter(classroom=self).count()

    @property
    def remaining_seats(self):
        return max(0, self.total_seats - self.occupied_seats)

    class Meta:
        unique_together = ['standard', 'division'] 
        ordering = ['standard', 'division']

    def save(self, *args, **kwargs):
        if self.stream:
            self.name = f"{self.standard}-{self.division} ({self.stream.name})"
        else:
            self.name = f"{self.standard}-{self.division}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

# 2. ADMISSION APPLICATION (The Funnel)
class AdmissionApplication(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending Review'), 
        ('Under_Review', 'Documents Verified'),
        ('Approved', 'Offer Letter Sent'), 
        ('Admitted', 'Fee Paid & Enrolled'),
        ('Rejected', 'Rejected'), 
        ('Waitlist', 'Waitlisted'),
    ]
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]

    admitted_student = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='admission_application')
    student_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    class_applied = models.ForeignKey(ClassRoom, on_delete=models.CASCADE)
    parent_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    previous_school = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    applied_date = models.DateTimeField(auto_now_add=True)
    rejection_reason = models.TextField(blank=True, null=True)

    # --- NEW DOCUMENTS ---
    passport_photo = models.ImageField(upload_to='admission_docs/photos/', blank=True, null=True)
    id_proof = models.FileField(upload_to='admission_docs/id_proofs/', blank=True, null=True)
    previous_mark_sheet = models.FileField(upload_to='admission_docs/marks/', blank=True, null=True)
    transfer_certificate = models.FileField(upload_to='admission_docs/tc/', blank=True, null=True)

    # --- ACADEMIC FIELDS ---
    stream_applied = models.ForeignKey(Stream, on_delete=models.SET_NULL, null=True)
    
    first_language = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, related_name='app_first_lang', limit_choices_to={'subject_type': 'Language'})
    second_language = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, related_name='app_second_lang', limit_choices_to={'subject_type': 'Language'})
    optional_subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, related_name='app_optional', limit_choices_to={'subject_type': 'Elective'})

    def __str__(self):
        return f"{self.student_name} ({self.class_applied.name})"

# 3. STUDENT PROFILE
class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    admission_number = models.CharField(max_length=20, unique=True)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.SET_NULL, null=True)
    
    stream = models.ForeignKey(Stream, on_delete=models.SET_NULL, null=True)
    first_language = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, related_name='profile_lang1')
    second_language = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, related_name='profile_lang2')
    optional_subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, related_name='profile_optional')
    
    roll_number = models.IntegerField(null=True, blank=True)
    father_name = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.admission_number} - {self.user.get_full_name()}"

# 4. DOCUMENTS
class AdmissionDocument(models.Model):
    application = models.ForeignKey(AdmissionApplication, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50)
    file = models.FileField(upload_to='admission_docs/')

    def __str__(self):
        return f"{self.document_type} for {self.application.student_name}"