from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

# Import related models
from admission.models import ClassRoom
from school_system.models import Subject 

# 1. DEPARTMENTS
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    head_of_department = models.ForeignKey('Staff', on_delete=models.SET_NULL, null=True, blank=True, related_name='hod_of')

    def __str__(self):
        return self.name

# 2. STAFF PROFILE
class Staff(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Resigned', 'Resigned'),
        ('On_Leave', 'On Leave'),
    ]

    # IDENTITY MATRIX CHOICES
    ROLE_CHOICES = [
        ('Teacher', 'Faculty Member'),
        ('Admin', 'Root Administrator'),
        ('Cashier', 'Financial Officer'),
        ('Librarian', 'Library Admin'),
        ('Office_Staff', 'Front Desk Operations'),
        ('Dept_Admin', 'Department Head'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    staff_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Teacher') # Added new role field
    
    qualification = models.CharField(max_length=100, null=True, blank=True)
    joining_date = models.DateField(default=timezone.now, null=True, blank=True)
    
    phone = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    is_teaching_staff = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')

    def save(self, *args, **kwargs):
        # NEW SAFETY NET: Auto-sync teaching flag based on role selection
        # This prevents mismatches if updated manually via Django Admin
        if self.role == 'Teacher':
            self.is_teaching_staff = True
        else:
            self.is_teaching_staff = False
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.staff_id}) - {self.role}"

# --- THE NUCLEAR FIX: Post-Save Signal with Dynamic Role Sync ---
@receiver(post_save, sender=Staff)
def sync_staff_user_role(sender, instance, created, **kwargs):
    """
    Automated Identity Provisioning:
    Using .set() ensures the User belongs ONLY to the Group 
    matching their current 'role' selection.
    """
    user = instance.user
    
    # 1. Force is_staff (Required for Sidebar & Admin Access)
    user.is_staff = True
    
    # 2. Get the specific group based on the staff's chosen role
    role_group, _ = Group.objects.get_or_create(name=instance.role)

    # 3. THE NUCLEAR MOVE: .set() clears all other groups and sets only the selected Role
    # This prevents a Cashier from accidentally having Teacher permissions, etc.
    user.groups.set([role_group])
    
    # 4. Save User changes
    user.save()

# 3. SUBJECT ALLOCATION
class SubjectAllocation(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='allocations')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE)
    academic_year = models.CharField(max_length=10, default='2025-2026')

    class Meta:
        unique_together = ['subject', 'classroom']
        verbose_name = "Subject Allocation"
        verbose_name_plural = "Subject Allocations"

    def __str__(self):
        return f"{self.staff.user.first_name} -> {self.subject.name} ({self.classroom.name})"