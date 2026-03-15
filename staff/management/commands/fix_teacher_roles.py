from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, User
from staff.models import Staff
from django.db import transaction

class Command(BaseCommand):
    help = 'Moves all users found in the Staff table from Student role to Teacher role.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Role Correction...'))

        # 1. Get or Create the necessary groups
        teacher_group, _ = Group.objects.get_or_create(name='Teacher')
        student_group = Group.objects.filter(name='Student').first()

        # 2. Get all Users who have a profile in the Staff table
        staff_users = User.objects.filter(staff__isnull=False)

        count = 0
        with transaction.atomic():
            for user in staff_users:
                # Add to Teacher Group
                if teacher_group not in user.groups.all():
                    user.groups.add(teacher_group)
                
                # Remove from Student Group if it exists
                if student_group and student_group in user.groups.all():
                    user.groups.remove(student_group)
                
                # Double check is_staff flag for admin access if needed
                user.is_staff = True
                user.save()
                
                self.stdout.write(f"Updated: {user.username} (Role: Teacher)")
                count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully updated {count} staff members to the Teacher role.'))