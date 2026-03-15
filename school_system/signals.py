from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from .models import Profile, Stream, Subject

# --- 1. USER PROFILE AUTOMATION ---

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Ensures every new User has a corresponding Profile object immediately.
    """
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Redundancy check to ensure the profile exists whenever the User is updated.
    RECURSION FIX: We use get_or_create instead of explicitly calling instance.profile.save().
    Calling save() here re-triggers the User save loop when last_login is updated during login.
    """
    Profile.objects.get_or_create(user=instance)


# --- 2. ROLE-BASED PERMISSION SYNC (Expanded for Staff Nodes) ---

@receiver(post_save, sender=Profile)
def sync_user_groups(sender, instance, **kwargs):
    """
    Whenever a Profile role is updated, move the User into the matching 
    Django Auth Group and toggle 'is_staff' for administrative access.
    """
    if instance.role:
        # 1. Identity Provisioning: Sync with Django Groups
        group, _ = Group.objects.get_or_create(name=instance.role)
        
        # 2. Access Control: Automatically set is_staff for all roles EXCEPT Student
        # This is essential for the Sidebar Logic in base.html to work
        user = instance.user
        should_have_access = instance.role in ['Admin', 'Teacher', 'Cashier', 'Librarian', 'Office_Staff', 'Dept_Admin']
        
        if user.is_staff != should_have_access:
            # We use update() here to prevent triggering save() signals recursively
            User.objects.filter(pk=user.pk).update(is_staff=should_have_access)
        
        # 3. Security Isolation: We use .set() so a user doesn't have overlapping roles
        # (e.g., A Cashier shouldn't also have Student permissions)
        user.groups.set([group])


# --- 3. ACADEMIC DATA INTEGRITY ---

@receiver(post_delete, sender=Stream)
def handle_stream_deletion(sender, instance, **kwargs):
    """
    Cleanup logic for when a Stream is deleted. 
    """
    print(f"Alert: Stream '{instance.name}' has been removed from the system.")


@receiver(post_save, sender=Subject)
def validate_subject_code(sender, instance, created, **kwargs):
    """
    Ensures subject codes are standardized for Kerala HSE reports.
    Example: 'phy' becomes 'PHY'
    """
    if instance.subject_code and not instance.subject_code.isupper():
        # Using update() to avoid recursion
        Subject.objects.filter(pk=instance.pk).update(
            subject_code=instance.subject_code.upper()
        )