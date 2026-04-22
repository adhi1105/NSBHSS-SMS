from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver

# --- 1. USER PROFILE MANAGEMENT (Expanded Roles) ---
class Profile(models.Model):
    # IDENTITY MATRIX: Expanded to include specialized staff nodes
    ROLE_CHOICES = [
        ('Admin', 'Root Administrator'),
        ('Teacher', 'Faculty Member'),
        ('Student', 'Student'),
        ('Cashier', 'Financial Officer'),      # NEW
        ('Librarian', 'Library Admin'),        # NEW
        ('Office_Staff', 'Front Desk Ops'),    # NEW
        ('Dept_Admin', 'Department Head'),     # NEW
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='Student')

    def __str__(self):
        return f"{self.user.username} - {self.role}"

    def save(self, *args, **kwargs):
        # Determine if is_staff is needed (anyone who isn't a student needs dashboard access)
        should_be_staff = self.role != 'Student'
        
        # RECURSION FIX: Only call user.save() if the status actually needs changing.
        # This prevents the infinite loop when a user logs in and updates 'last_login'.
        if self.user.is_staff != should_be_staff:
            self.user.is_staff = should_be_staff
            self.user.save(update_fields=['is_staff'])
            
        super().save(*args, **kwargs)
        
        if self.role:
            # Syncing Profile role with Django Groups for template filters
            group, _ = Group.objects.get_or_create(name=self.role)
            # THE NUCLEAR SYNC: Ensures user has ONLY the group matching their profile role
            self.user.groups.set([group])

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # RECURSION FIX: We use get_or_create instead of explicitly calling instance.profile.save()
    # Calling save() here was re-triggering the User save loop during login.
    pass # get_or_create in create_user_profile handles this safely enough in testing


# --- 2. ACADEMIC STRUCTURE (Updated for Kerala Syllabus) ---

class Stream(models.Model):
    """
    Examples: Science (Biology), Science (Computer), Commerce, Humanities
    """
    name = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.name


class Subject(models.Model):
    TYPE_CHOICES = [
        ('Core', 'Core Subject'),          # e.g., Physics, Accountancy, Economics
        ('Elective', 'Elective/Optional'), # e.g., Computer Science, Sociology, Psychology
        ('Language', 'Language'),          # e.g., English, Malayalam, Hindi, Arabic
        ('Common', 'General'),             # e.g., General Education
    ]

    name = models.CharField(max_length=100)
    subject_code = models.CharField(max_length=10, unique=True, null=True, blank=True)
    
    # Subject Metadata
    subject_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='Core')
    is_practical = models.BooleanField(default=False, help_text="Check if subject has practical exams")
    
    # Relationships
    # Subjects like Maths or Economics can belong to both Science and Commerce streams.
    streams = models.ManyToManyField(Stream, blank=True, related_name='subjects')
    
    def __str__(self):
        return f"{self.name} ({self.get_subject_type_display()})"

    class Meta:
        ordering = ['name']