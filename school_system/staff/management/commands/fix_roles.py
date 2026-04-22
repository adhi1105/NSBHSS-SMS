from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from staff.models import Staff

class Command(BaseCommand):
    help = 'Absolute override to fix roles bypassing all Django signals'

    def handle(self, *args, **kwargs):
        teacher_group, _ = Group.objects.get_or_create(name='Teacher')
        
        # Get every User that has a linked Staff profile
        staff_users = User.objects.filter(staff__isnull=False)
        
        count = 0
        for user in staff_users:
            # 1. Use .update() to change permissions WITHOUT triggering signals
            User.objects.filter(id=user.id).update(is_staff=True, is_superuser=False)
            
            # 2. Directly clear and force the group at the database join-table level
            user.groups.clear()
            user.groups.add(teacher_group)
            
            count += 1

        self.stdout.write(self.style.SUCCESS(f"🚀 SUCCESS: {count} teachers have been forcefully locked into the Teacher role."))