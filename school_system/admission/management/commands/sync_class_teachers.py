import os
from django.core.management.base import BaseCommand
from django.db import transaction
from admission.models import ClassRoom
from staff.models import SubjectAllocation, Staff

class Command(BaseCommand):
    help = 'Automatically assigns Core Subject teachers as Class Teachers for their respective classes.'

    def handle(self, *args, **options):
        # 1. Define what counts as a 'Core Subject' for Class Teacher eligibility
        CORE_SUBJECTS = [
            'Physics', 'Chemistry', 'Biology', 'Mathematics', 
            'English', 'Accountancy', 'Business Studies', 'Economics', 
            'History', 'Political Science', 'Sociology', 'Home Science'
        ]

        self.stdout.write(self.style.SUCCESS('Starting Class Teacher Sync...'))

        with transaction.atomic():
            # 2. Get list of teachers already assigned to ANY class to avoid double-booking
            already_assigned_ids = list(
                ClassRoom.objects.exclude(class_teacher=None)
                .values_list('class_teacher_id', flat=True)
            )

            # 3. Fetch classrooms that currently have no teacher assigned
            unassigned_rooms = ClassRoom.objects.filter(class_teacher=None)
            
            if not unassigned_rooms.exists():
                self.stdout.write("All classes already have teachers assigned.")
                return

            for room in unassigned_rooms:
                self.stdout.write(f"Processing Class: {room.name}...")

                # 4. Find teachers teaching Core Subjects in THIS specific class
                # We filter SubjectAllocation by this classroom AND our core list
                eligible_allocations = SubjectAllocation.objects.filter(
                    classroom=room,
                    subject__name__in=CORE_SUBJECTS
                ).select_related('staff__user').exclude(staff_id__in=already_assigned_ids)

                # 5. Assign the first eligible teacher found
                target_allocation = eligible_allocations.first()

                if target_allocation:
                    teacher = target_allocation.staff
                    room.class_teacher = teacher
                    room.save()

                    # Add to the exclusion list so they aren't picked for another class
                    already_assigned_ids.append(teacher.id)
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✅ Assigned {teacher.user.get_full_name()} ({target_allocation.subject.name}) to {room.name}"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"  ⚠️ No available Core Teacher found for {room.name}")
                    )

        self.stdout.write(self.style.SUCCESS('Sync Complete!'))