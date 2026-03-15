from django.core.management.base import BaseCommand
from school_system.models import Subject
from staff.models import SubjectAllocation
from timetable.models import TimetableEntry
from django.db import transaction

class Command(BaseCommand):
    help = 'Merges languages and removes unwanted elective subjects'

    def handle(self, *args, **options):
        with transaction.atomic():
            # 1. DELETE UNWANTED SUBJECTS
            to_delete = ['Arabic', 'Computer Applications']
            Subject.objects.filter(name__in=to_delete).delete()
            self.stdout.write(self.style.SUCCESS("Deleted Arabic and Computer Applications."))

            # 2. PREPARE THE MASTER LANGUAGE
            target_name = "Malayalam/Hindi"
            lang_master, _ = Subject.objects.get_or_create(name=target_name)
            
            # Find old language subjects
            old_langs = Subject.objects.filter(name__in=['Malayalam', 'Hindi']).exclude(id=lang_master.id)

            for old_sub in old_langs:
                self.stdout.write(f"Merging {old_sub.name} into {target_name}...")
                
                # Get all allocations for the old subject
                old_allocations = SubjectAllocation.objects.filter(subject=old_sub)

                for alloc in old_allocations:
                    # Check if an allocation for the NEW master subject already exists in this classroom
                    exists = SubjectAllocation.objects.filter(
                        classroom=alloc.classroom, 
                        subject=lang_master
                    ).exists()

                    if exists:
                        # If it exists, just delete the old one to avoid IntegrityError
                        alloc.delete()
                    else:
                        # If no master exists yet, move this one to the master
                        alloc.subject = lang_master
                        alloc.save()

                # Update Timetable entries (Safe to bulk update as there's no unique constraint on these fields)
                TimetableEntry.objects.filter(subject=old_sub).update(subject=lang_master)
                
                # Finally, remove the old specific subject name
                old_sub.delete()

        self.stdout.write(self.style.SUCCESS("Purge and Merge completed without conflicts!"))