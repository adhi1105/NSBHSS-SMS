from django.db import models
from django.contrib.auth.models import User
from admission.models import ClassRoom
from school_system.models import Stream, Subject

class Student(models.Model):
    # --- STATUS CHOICES ---
    STUDENT_STATUS = [
        ('pursuing', 'Pursuing'),
        ('passed_out', 'Passed Out'),
        ('discontinued', 'Discontinued'),
        ('on_leave', 'On Leave'),
        ('suspended', 'Suspended'),
    ]

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    # --- CORE RELATIONSHIP ---
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='student_profile'
    )
    student_id = models.CharField(
        max_length=20, 
        unique=True, 
        help_text="Unique Institutional ID (e.g., STU2026001)"
    )
    
    # --- ACADEMIC INFO ---
    classroom = models.ForeignKey(
        ClassRoom, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='students'
    )
    roll_number = models.IntegerField(null=True, blank=True)
    admission_date = models.DateField(auto_now_add=True)
    
    # --- SUBJECT & STREAM MAPPING ---
    # Aligned with school_system.Stream and Subject models
    stream = models.ForeignKey(
        Stream, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    first_language = models.ForeignKey(
        Subject, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='student_first_lang'
    )
    second_language = models.ForeignKey(
        Subject, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='student_second_lang'
    )
    optional_subject = models.ForeignKey(
        Subject, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='student_optional'
    )

    # --- STATUS & TRACKING ---
    status = models.CharField(
        max_length=20, 
        choices=STUDENT_STATUS, 
        default='pursuing', 
        db_index=True
    )
    is_active = models.BooleanField(
        default=True, 
        help_text="Uncheck this to disable login access for this student."
    )
    
    # --- PERSONAL INFO ---
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='M')
    blood_group = models.CharField(max_length=5, blank=True)
    
    # Family & Contact
    father_name = models.CharField(max_length=100)
    mother_name = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=15, blank=True)
    primary_phone = models.CharField(max_length=15, blank=True) 
    address = models.TextField()

    # --- DOCUMENTS & UPLOADS ---
    # These fields match the AdmissionApplication document fields for easy transfer
    photo = models.ImageField(
        upload_to='student_photos/', 
        null=True, 
        blank=True, 
        help_text="Passport Size Photo"
    )
    id_proof = models.FileField(
        upload_to='student_docs/id_proofs/', 
        null=True, 
        blank=True, 
        help_text="Aadhar/Passport/ID Card"
    )
    previous_mark_sheet = models.FileField(
        upload_to='student_docs/mark_sheets/', 
        null=True, 
        blank=True
    )
    transfer_certificate = models.FileField(
        upload_to='student_docs/tc/', 
        null=True, 
        blank=True
    )

    class Meta:
        verbose_name = "Student Profile"
        verbose_name_plural = "Student Profiles"
        ordering = ['student_id']

    def __str__(self):
        return f"{self.student_id} - {self.user.get_full_name()}"

    @property
    def get_full_name(self):
        return self.user.get_full_name()