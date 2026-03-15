import os
import re  
from django.db import models
from django.contrib.auth.models import User

# Corrected Imports based on your app structure
from admission.models import ClassRoom
from student_info.models import Student  
from school_system.models import Stream, Subject 

# --- 1. COURSE ---
class Course(models.Model):
    title = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True, help_text="e.g. PHY-10")
    
    stream = models.ForeignKey(Stream, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses')
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='courses_taught')
    
    description = models.TextField(blank=True)
    thumbnail = models.ImageField(upload_to='courses/thumbnails/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.classroom.name})"

# --- 2. LESSON ---
class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True, help_text="Text content or summary of the lesson")
    order = models.PositiveIntegerField(default=1)
    
    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.order}. {self.title}"

# --- 3. VIDEO SUB-MODEL (Fixed for Error 153) ---
class LessonVideo(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='videos')
    title = models.CharField(max_length=200, blank=True)
    youtube_url = models.URLField(help_text="YouTube Video URL")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def get_embed_url(self):
        """
        Extracts 11-char ID and forces a secure, clean embed format.
        Prevents Error 153 by stripping all extra URL parameters.
        """
        if not self.youtube_url: return ""
        
        # Aggressive Regex to find only the video ID
        regex = r'(?:v=|\/|be\/|embed\/)([a-zA-Z0-9_-]{11})'
        match = re.search(regex, self.youtube_url)
        
        if match:
            video_id = match.group(1)
            # enablejsapi=1 and origin are key for browser security handshake
            return f"https://www.youtube.com/embed/{video_id}?rel=0&enablejsapi=1&modestbranding=1"
        return ""

# --- 4. STUDY MATERIAL ---
class StudyMaterial(models.Model):
    MATERIAL_TYPES = [('pdf', 'PDF'), ('ppt', 'PPT'), ('video', 'Video'), ('link', 'Link')]
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200)
    file_type = models.CharField(max_length=10, choices=MATERIAL_TYPES)
    file_upload = models.FileField(upload_to='lms_materials/', blank=True, null=True)
    external_link = models.URLField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def file_name(self):
        return os.path.basename(self.file_upload.name) if self.file_upload else ""

# --- 5. ASSIGNMENT ---
class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateTimeField()
    total_marks = models.PositiveIntegerField(default=100)
    file_upload = models.FileField(upload_to='assignments/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# --- 6. STUDENT SUBMISSION & GRADING ---
class StudentSubmission(models.Model):
    STATUS_CHOICES = [('submitted', 'Submitted'), ('graded', 'Graded')]

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='submissions')
    file = models.FileField(upload_to='submissions/')
    student_comment = models.TextField(blank=True)
    
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    teacher_remarks = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('assignment', 'student')

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.assignment.title}"